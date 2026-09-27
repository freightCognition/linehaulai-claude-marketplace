# Admin API Reference

All methods below live on `*slack.Client`, require an **org-level admin/owner token** on an **Enterprise Grid** workspace, and take `context.Context` as the first parameter. Regular bot tokens (`xoxb-`) will fail authentication even with broad scopes.

## Conversations (`admin.conversations.*`)

### Invite, Archive, Rename, Delete

```go
err := adminAPI.AdminConversationsInvite(ctx, slack.AdminConversationsInviteParams{
    ChannelID: channelID,
    UserIDs:   []string{userID},
})

err = adminAPI.AdminConversationsArchive(ctx, channelID)
err = adminAPI.AdminConversationsUnarchive(ctx, channelID)
err = adminAPI.AdminConversationsRename(ctx, channelID, "incident-2024-01")
err = adminAPI.AdminConversationsDelete(ctx, channelID)
```

### Create a Channel Org-Wide

```go
channelID, err := adminAPI.AdminConversationsCreate(ctx, "eng-announcements", false,
    slack.AdminConversationsCreateOptionDescription("Engineering-wide announcements"),
    slack.AdminConversationsCreateOptionOrgWide(true),
)
```

### Disconnect a Shared Channel

```go
err := adminAPI.AdminConversationsDisconnectShared(ctx, channelID,
    slack.AdminConversationsDisconnectSharedOptionLeavingTeamIDs([]string{teamID}),
)
```

### Search and Lookup

```go
results, err := adminAPI.AdminConversationsSearch(ctx,
    slack.AdminConversationsSearchOptionTeamIDs([]string{teamID}),
    slack.AdminConversationsSearchOptionQuery("incident"),
    slack.AdminConversationsSearchOptionSearchChannelTypes([]string{"private"}),
    slack.AdminConversationsSearchOptionLimit(100),
)

channelIDs, nextCursor, err := adminAPI.AdminConversationsLookup(ctx,
    []string{teamID},
    0, // lastMessageActivityBefore, unix timestamp, 0 = no filter
    slack.AdminConversationsLookupOptionLimit(100),
)
```

### Bulk Operations

```go
err := adminAPI.AdminConversationsBulkArchive(ctx, []string{"C111", "C222"})
err = adminAPI.AdminConversationsBulkDelete(ctx, []string{"C111", "C222"})
err = adminAPI.AdminConversationsBulkMove(ctx, slack.AdminConversationsBulkMoveParams{
    ChannelIDs:   []string{"C111", "C222"},
    TargetTeamID: teamID,
})
```

### Conversation Preferences and Retention

```go
prefs, err := adminAPI.AdminConversationsGetConversationPrefs(ctx, channelID)

err = adminAPI.AdminConversationsSetConversationPrefs(ctx, slack.AdminConversationsSetConversationPrefsParams{
    ChannelID: channelID,
    // Name/Value depend on the specific preference being set
})

retention, err := adminAPI.AdminConversationsGetCustomRetention(ctx, channelID)
err = adminAPI.AdminConversationsSetCustomRetention(ctx, channelID, 90) // days
err = adminAPI.AdminConversationsRemoveCustomRetention(ctx, channelID)
```

### Team Assignment and Visibility

```go
err := adminAPI.AdminConversationsSetTeams(ctx, slack.AdminConversationsSetTeamsParams{
    ChannelID:     channelID,
    TargetTeamIDs: []string{teamID},
})

teamIDs, nextCursor, err := adminAPI.AdminConversationsGetTeams(ctx, slack.AdminConversationsGetTeamsParams{
    ChannelID: channelID,
})

err = adminAPI.AdminConversationsConvertToPrivate(ctx, channelID)
err = adminAPI.AdminConversationsConvertToPublic(ctx, channelID)
```

### Restrict Access (Channel-Level Groups)

```go
err := adminAPI.AdminConversationsRestrictAccessAddGroup(ctx, channelID, groupID)
groupIDs, err := adminAPI.AdminConversationsRestrictAccessListGroups(ctx, channelID)
err = adminAPI.AdminConversationsRestrictAccessRemoveGroup(ctx, channelID, groupID)
```

### EKM (Enterprise Key Management)

```go
info, err := adminAPI.AdminConversationsEKMListOriginalConnectedChannelInfo(ctx)
```

## Roles (`admin.roles.*`)

```go
resp, err := adminAPI.AdminRolesAddAssignments(ctx, slack.AdminRolesAddAssignmentsParams{
    RoleID:    roleID,
    EntityIDs: []string{teamID},
    UserIDs:   []string{userID},
})
// resp may include RejectedUsers/RejectedEntities for partial failures

assignments, err := adminAPI.AdminRolesListAssignments(ctx,
    slack.AdminRolesListAssignmentsOptionRoleIDs([]string{roleID}),
    slack.AdminRolesListAssignmentsOptionLimit(100),
)

resp, err = adminAPI.AdminRolesRemoveAssignments(ctx, slack.AdminRolesRemoveAssignmentsParams{
    RoleID:    roleID,
    EntityIDs: []string{teamID},
    UserIDs:   []string{userID},
})
```

## Teams (`admin.teams.settings.*`)

```go
settings, err := adminAPI.AdminTeamsSettingsInfo(ctx, teamID)

err = adminAPI.AdminTeamsSettingsSetName(ctx, teamID, "Engineering")
err = adminAPI.AdminTeamsSettingsSetDescription(ctx, teamID, "Engineering workspace")
err = adminAPI.AdminTeamsSettingsSetIcon(ctx, teamID, "https://example.com/icon.png")
err = adminAPI.AdminTeamsSettingsSetDefaultChannels(ctx, teamID, "C_GENERAL", "C_ANNOUNCEMENTS")
err = adminAPI.AdminTeamsSettingsSetDiscoverability(ctx, teamID, slack.TeamDiscoverabilityInviteOnly)
```

`TeamDiscoverability` values: `TeamDiscoverabilityOpen`, `TeamDiscoverabilityInviteOnly`, `TeamDiscoverabilityClosed`, `TeamDiscoverabilityUnlisted`.

## Production Patterns

### Guard Against Non-Admin Tokens

```go
func newAdminClient() (*slack.Client, error) {
    token := os.Getenv("SLACK_ORG_ADMIN_TOKEN")
    if token == "" {
        return nil, fmt.Errorf("SLACK_ORG_ADMIN_TOKEN not set")
    }
    return slack.New(token), nil
}
```

### Confirm Before Bulk Deletes

```go
func bulkDeleteChannels(ctx context.Context, api *slack.Client, channelIDs []string, confirmed bool) error {
    if !confirmed {
        return fmt.Errorf("refusing to bulk-delete %d channels without explicit confirmation", len(channelIDs))
    }
    return api.AdminConversationsBulkDelete(ctx, channelIDs)
}
```

## Common Pitfalls

1. **Wrong token type** — admin methods require an org-level admin/owner token, not a bot token
2. **Non-Enterprise-Grid workspaces** — most admin methods 404 or error outside Enterprise Grid
3. **Irreversible bulk operations** — `AdminConversationsBulkDelete` cannot be undone; gate it behind explicit confirmation
4. **No `admin.users.*` wrapper** — user provisioning/deprovisioning admin endpoints aren't wrapped as Go methods in this SDK version; call the REST API directly if needed
5. **Cursor-based pagination** — `AdminConversationsSearch`, `AdminConversationsLookup`, and `AdminRolesListAssignments` all paginate; loop until the cursor is empty
