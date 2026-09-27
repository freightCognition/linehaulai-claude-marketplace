# Canvas API

Canvas is Slack's flexible-document surface. Every method has a `*Context` variant (recommended) and a legacy variant that runs against `context.Background()`.

## Create a Canvas

```go
canvasID, err := api.CreateCanvasContext(ctx, "Sprint Planning", slack.DocumentContent{
    Type:     "markdown",
    Markdown: "# Sprint Planning\n\n## Goals\n- Ship the retry config docs",
})
if err != nil {
    return err
}
```

## Edit a Canvas

Edits are applied as a list of operations:

```go
err := api.EditCanvasContext(ctx, slack.EditCanvasParams{
    CanvasID: canvasID,
    Changes: []slack.CanvasChange{
        {
            Operation: "insert_after",
            SectionID: sectionID,
            DocumentContent: slack.DocumentContent{
                Type:     "markdown",
                Markdown: "## New Section\nAdded via the API",
            },
        },
    },
})
```

Common `Operation` values: `insert_after`, `insert_before`, `insert_at_start`, `insert_at_end`, `replace`, `delete`.

## Delete a Canvas

```go
err := api.DeleteCanvasContext(ctx, canvasID)
```

## Manage Access

```go
err := api.SetCanvasAccessContext(ctx, slack.SetCanvasAccessParams{
    CanvasID:    canvasID,
    AccessLevel: "write", // or "read"
    ChannelIDs:  []string{"C1234567890"},
    UserIDs:     []string{"U1234567890"},
})

err = api.DeleteCanvasAccessContext(ctx, slack.DeleteCanvasAccessParams{
    CanvasID: canvasID,
    UserIDs:  []string{"U1234567890"},
})
```

## Look Up Sections

Used to find `SectionID` values before editing:

```go
sections, err := api.LookupCanvasSectionsContext(ctx, slack.LookupCanvasSectionsParams{
    CanvasID: canvasID,
    Criteria: slack.LookupCanvasSectionsCriteria{
        ContainsText: "Goals",
    },
})
for _, s := range sections {
    fmt.Println(s.ID)
}
```

## Common Pitfalls

- Prefer the `*Context` variants — the non-context methods just call `context.Background()` internally and give you no cancellation control
- `EditCanvasContext` requires a valid `SectionID` for most operations except `insert_at_start`/`insert_at_end` — look it up first with `LookupCanvasSectionsContext`
- Canvas access levels are channel/user scoped, not workspace-wide — set access explicitly per audience
