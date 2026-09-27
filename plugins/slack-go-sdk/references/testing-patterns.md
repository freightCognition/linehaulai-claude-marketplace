# Testing Patterns for Slack Go Applications

## The slacktest Package (Preferred for Bot Integration Tests)

The SDK ships `github.com/slack-go/slack/slacktest`, a mock HTTP + WebSocket server that stands in for the real Slack API — prefer this over hand-rolled mocks for anything that exercises RTM/messaging behavior.

```go
import (
    "testing"

    "github.com/slack-go/slack"
    "github.com/slack-go/slack/slacktest"
)

func TestBotRespondsToMessage(t *testing.T) {
    server := slacktest.NewTestServer()
    server.SetBotName("mybot")
    go server.Start()
    defer server.Stop()

    api := slack.New("test-token", slack.OptionAPIURL(server.GetAPIURL()))

    rtm := server.GetTestRTMInstance()
    go rtm.ManageConnection()

    server.SendMessageToBot("C1234567890", "hello bot")

    if !server.SawOutgoingMessage("some expected reply") {
        t.Errorf("expected bot to reply, but it didn't")
    }
}
```

Useful `*slacktest.Server` methods:

- `GetAPIURL()` / `GetWSURL()` — point a real `*slack.Client`/RTM connection at the mock server
- `SendMessageToBot(channel, msg)` / `SendDirectMessageToBot(msg)` — simulate inbound messages
- `SawMessage(msg)` / `SawOutgoingMessage(msg)` — assert on messages seen by the server
- `GetChannels()` / `GetGroups()` — inspect the mock workspace's seeded state
- `SetBotName(name)` — configure the bot identity the server reports

This exercises real `slack.Client`/RTM wire behavior (JSON payloads, WebSocket framing) instead of just your own interface, catching integration bugs that pure interface mocks miss.

## Mocking the Slack API Client

Use interface-based mocking below for pure unit tests where you don't need real wire-level behavior — reach for `slacktest` above when you do.

### Interface-Based Mocking

Define an interface for the Slack client operations you use:

```go
package slack

// Client interface wraps common Slack API operations
type Client interface {
    PostMessage(channelID string, options ...MsgOption) (string, string, error)
    GetUserInfo(user string) (*User, error)
    GetConversationHistory(params *GetConversationHistoryParameters) (*GetConversationHistoryResponse, error)
}

// Ensure slack.Client implements our interface
var _ Client = (*slack.Client)(nil)
```

Create a mock implementation:

```go
package mocks

type MockSlackClient struct {
    PostMessageFunc            func(string, ...slack.MsgOption) (string, string, error)
    GetUserInfoFunc            func(string) (*slack.User, error)
    GetConversationHistoryFunc func(*slack.GetConversationHistoryParameters) (*slack.GetConversationHistoryResponse, error)
}

func (m *MockSlackClient) PostMessage(channelID string, options ...slack.MsgOption) (string, string, error) {
    if m.PostMessageFunc != nil {
        return m.PostMessageFunc(channelID, options...)
    }
    return "ts_12345", "C1234567890", nil
}

func (m *MockSlackClient) GetUserInfo(user string) (*slack.User, error) {
    if m.GetUserInfoFunc != nil {
        return m.GetUserInfoFunc(user)
    }
    return &slack.User{ID: user, Name: "testuser"}, nil
}
```

Usage in tests:

```go
func TestMessageHandler(t *testing.T) {
    mockClient := &mocks.MockSlackClient{
        PostMessageFunc: func(channelID string, options ...slack.MsgOption) (string, string, error) {
            if channelID != "C1234567890" {
                t.Errorf("unexpected channel: %s", channelID)
            }
            return "ts_12345", channelID, nil
        },
    }

    handler := NewMessageHandler(mockClient)
    err := handler.SendWelcomeMessage("C1234567890", "U1234567890")
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
}
```

## Integration Testing

### Test Against Slack Test Workspace

Create a dedicated test workspace for integration tests:

```go
// +build integration

package integration_test

import (
    "os"
    "testing"
    "github.com/slack-go/slack"
)

func TestPostMessageIntegration(t *testing.T) {
    token := os.Getenv("SLACK_TEST_TOKEN")
    if token == "" {
        t.Skip("SLACK_TEST_TOKEN not set")
    }

    channelID := os.Getenv("SLACK_TEST_CHANNEL")
    if channelID == "" {
        t.Skip("SLACK_TEST_CHANNEL not set")
    }

    api := slack.New(token)

    _, _, err := api.PostMessage(
        channelID,
        slack.MsgOptionText("Integration test message", false),
    )
    if err != nil {
        t.Fatalf("failed to post message: %v", err)
    }
}
```

Run integration tests separately:

```bash
go test -tags=integration ./...
```

## Test Fixtures

Create reusable test fixtures for common Slack events:

```go
package fixtures

import "github.com/slack-go/slack/slackevents"

func NewMessageEvent(channel, user, text string) *slackevents.MessageEvent {
    return &slackevents.MessageEvent{
        Type:    "message",
        Channel: channel,
        User:    user,
        Text:    text,
        TimeStamp: "1234567890.123456",
    }
}

func NewAppMentionEvent(channel, user, text string) *slackevents.AppMentionEvent {
    return &slackevents.AppMentionEvent{
        Type:           "app_mention",
        Channel:        channel,
        User:           user,
        Text:           text,
        TimeStamp:      "1234567890.123456",
        EventTimeStamp: "1234567890.123456",
    }
}
```

Usage:

```go
func TestHandleMessage(t *testing.T) {
    event := fixtures.NewMessageEvent("C123", "U456", "Hello bot!")

    handler := NewEventHandler(mockClient)
    err := handler.HandleMessage(event)
    // assertions...
}
```

## Table-Driven Tests

Test multiple scenarios efficiently:

```go
func TestMessageFormatter(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {
            name:     "simple text",
            input:    "hello",
            expected: "hello",
        },
        {
            name:     "user mention",
            input:    "<@U123>",
            expected: "@user123",
        },
        {
            name:     "channel mention",
            input:    "<#C123>",
            expected: "#general",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := formatMessage(tt.input)
            if result != tt.expected {
                t.Errorf("got %q, want %q", result, tt.expected)
            }
        })
    }
}
```

## CI/CD Testing Recommendations

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run unit tests
        run: go test -v -race -coverprofile=coverage.out ./...

      - name: Run integration tests
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          SLACK_TEST_TOKEN: ${{ secrets.SLACK_TEST_TOKEN }}
          SLACK_TEST_CHANNEL: ${{ secrets.SLACK_TEST_CHANNEL }}
        run: go test -v -tags=integration ./...

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out
```

## Best Practices

1. **Use interfaces** for dependency injection and mocking
2. **Separate unit and integration tests** with build tags
3. **Create test fixtures** for common event types
4. **Use table-driven tests** for multiple scenarios
5. **Mock external dependencies** in unit tests
6. **Test against real Slack API** in integration tests (dedicated workspace)
7. **Track code coverage** and aim for >80%
8. **Run tests in CI/CD** pipeline
