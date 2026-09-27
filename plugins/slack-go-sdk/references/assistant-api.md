# Assistant API

The Assistant API supports building an **AI Assistant app** inside Slack (the assistant-thread surface in the Slack UI) — it is not a general chat-completions or LLM-calling API. Every method has a `*Context` variant (recommended) and a legacy variant.

## Set Thread Status

Show a "thinking" indicator while your assistant works:

```go
err := api.SetAssistantThreadsStatusContext(ctx, slack.AssistantThreadsSetStatusParameters{
    ChannelID: channelID,
    ThreadTS:  threadTS,
    Status:    "is thinking...",
})
```

Clear it by setting `Status` to an empty string once you have a response.

## Set Thread Title

```go
err := api.SetAssistantThreadsTitleContext(ctx, slack.AssistantThreadsSetTitleParameters{
    ChannelID: channelID,
    ThreadTS:  threadTS,
    Title:     "Investigate deploy failure",
})
```

## Suggested Prompts

```go
params := slack.AssistantThreadsSetSuggestedPromptsParameters{
    ChannelID: channelID,
    ThreadTS:  threadTS,
    Title:     "Try asking:",
}
params.AddPrompt("Check deploy status", "What's the status of the latest deploy?")
params.AddPrompt("Show recent errors", "Show me errors from the last hour")

err := api.SetAssistantThreadsSuggestedPromptsContext(ctx, params)
```

## Search Assistant Context

Lets an assistant search across messages/files/channels the requesting user can access, to ground a response:

```go
results, err := api.SearchAssistantContextContext(ctx, slack.AssistantSearchContextParameters{
    Query:        "deploy failure",
    ChannelTypes: []string{"public_channel", "private_channel"},
    ContentTypes: []string{"messages"},
    Limit:        20,
})
```

## Common Pitfalls

- This is not a wrapper around any external LLM provider — it only manages the Slack-side assistant thread UI (status, title, suggested prompts) and lets you search Slack content for context; your own model call happens outside the SDK
- `ChannelID` + `ThreadTS` must match an active assistant thread — calling these methods outside that context will fail
- Clear the "thinking" status once your response is posted, or users will see a stuck loading indicator
