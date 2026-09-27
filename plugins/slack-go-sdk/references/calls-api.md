# Calls API

The Calls API lets a third-party calling app register call sessions in Slack so users can join from the Slack UI. Every method has a `*Context` variant (recommended) and a legacy variant.

## Register a Call

```go
call, err := api.AddCallContext(ctx, slack.AddCallParameters{
    JoinURL:          "https://calls.example.com/join/abc123", // required
    ExternalUniqueID: "call-abc123",                            // required
    CreatedBy:        "U1234567890",                            // required if using a bot token
    Title:            "Incident Review",
    DateStart:        slack.JSONTime(time.Now().Unix()),
    Participants: []slack.CallParticipant{
        {SlackID: "U1234567890"},
        {ExternalID: "ext-42", DisplayName: "Guest User"},
    },
})
if err != nil {
    return err
}
```

## Get / Update / End a Call

```go
current, err := api.GetCallContext(ctx, call.ID)

updated, err := api.UpdateCallContext(ctx, call.ID, slack.UpdateCallParameters{
    Title: "Incident Review (extended)",
})

err = api.EndCallContext(ctx, call.ID, slack.EndCallParameters{
    Duration: 45 * time.Minute,
})
```

## Manage Participants

```go
err := api.CallAddParticipantsContext(ctx, call.ID, []slack.CallParticipant{
    {SlackID: "U2222222222"},
})

err = api.CallRemoveParticipantsContext(ctx, call.ID, []slack.CallParticipant{
    {SlackID: "U2222222222"},
})
```

`CallParticipant` needs at least one of `SlackID` or `ExternalID` — a participant with neither set is invalid.

## Common Pitfalls

- `JoinURL`, `ExternalUniqueID`, and (for bot tokens) `CreatedBy` are required on `AddCall` — omitting them returns an API error
- `ExternalUniqueID` must stay stable for the lifetime of the call if you need to reconcile it against your own calling system's records
- The Calls API registers metadata about a call happening elsewhere — it does not provide Slack-hosted audio/video itself
