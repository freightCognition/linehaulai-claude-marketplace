---
name: slack-admin-api
description: Enterprise Grid Admin API operations with the Slack Go SDK. Use when managing organization-wide conversations, assigning or listing admin roles, configuring team settings, restricting channel access, or building internal tooling for Slack workspace/org administrators.
keywords: [slack, admin, enterprise-grid, roles, teams, conversations]
---

# Slack Admin API

## Prerequisites

Admin API methods require an **org-level admin/owner token**, not a regular bot token, and only work on **Enterprise Grid** workspaces. A bot token will fail auth even with broad bot scopes. Every admin method takes `context.Context` as its first argument.

```go
adminAPI := slack.New(os.Getenv("SLACK_ORG_ADMIN_TOKEN"))
```

## Conversations Administration

### Search Conversations Org-Wide

```go
results, err := adminAPI.AdminConversationsSearch(ctx,
    slack.AdminConversationsSearchOptionTeamIDs([]string{"T1234567890"}),
    slack.AdminConversationsSearchOptionQuery("incident"),
    slack.AdminConversationsSearchOptionLimit(50),
)
if err != nil {
    return err
}
```

### Archive, Rename, Delete

```go
err := adminAPI.AdminConversationsArchive(ctx, channelID)
err = adminAPI.AdminConversationsRename(ctx, channelID, "new-channel-name")
err = adminAPI.AdminConversationsDelete(ctx, channelID)
```

### Move a Channel Between Teams

```go
err := adminAPI.AdminConversationsSetTeams(ctx, slack.AdminConversationsSetTeamsParams{
    ChannelID:     channelID,
    TargetTeamIDs: []string{"T0987654321"},
})
```

### Bulk Operations

```go
err := adminAPI.AdminConversationsBulkArchive(ctx, []string{"C111", "C222"})
err = adminAPI.AdminConversationsBulkDelete(ctx, []string{"C111", "C222"})
err = adminAPI.AdminConversationsBulkMove(ctx, slack.AdminConversationsBulkMoveParams{
    ChannelIDs:   []string{"C111", "C222"},
    TargetTeamID: "T0987654321",
})
```

### Restrict Access to a Channel

```go
err := adminAPI.AdminConversationsRestrictAccessAddGroup(ctx, channelID, groupID)
groups, err := adminAPI.AdminConversationsRestrictAccessListGroups(ctx, channelID)
err = adminAPI.AdminConversationsRestrictAccessRemoveGroup(ctx, channelID, groupID)
```

See [admin-api-reference.md](../../references/admin-api-reference.md) for the full conversations, roles, and teams surface, including retention, EKM, and invite/lookup methods.

## Roles Administration

Assign or remove admin/owner-style roles for users:

```go
_, err := adminAPI.AdminRolesAddAssignments(ctx, slack.AdminRolesAddAssignmentsParams{
    RoleID:    roleID,
    EntityIDs: []string{teamID},
    UserIDs:   []string{userID},
})

assignments, err := adminAPI.AdminRolesListAssignments(ctx,
    slack.AdminRolesListAssignmentsOptionRoleIDs([]string{roleID}),
)

_, err = adminAPI.AdminRolesRemoveAssignments(ctx, slack.AdminRolesRemoveAssignmentsParams{
    RoleID:    roleID,
    EntityIDs: []string{teamID},
    UserIDs:   []string{userID},
})
```

## Team Settings Administration

```go
settings, err := adminAPI.AdminTeamsSettingsInfo(ctx, teamID)

err = adminAPI.AdminTeamsSettingsSetName(ctx, teamID, "Engineering")
err = adminAPI.AdminTeamsSettingsSetDescription(ctx, teamID, "Engineering workspace")
err = adminAPI.AdminTeamsSettingsSetIcon(ctx, teamID, iconURL)
err = adminAPI.AdminTeamsSettingsSetDefaultChannels(ctx, teamID, "C_GENERAL", "C_ANNOUNCEMENTS")
err = adminAPI.AdminTeamsSettingsSetDiscoverability(ctx, teamID, slack.TeamDiscoverabilityInviteOnly)
```

`TeamDiscoverability` is one of `TeamDiscoverabilityOpen`, `TeamDiscoverabilityInviteOnly`, `TeamDiscoverabilityClosed`, or `TeamDiscoverabilityUnlisted`.

## Common Pitfalls

- Using a bot token instead of an org-level admin token — admin methods will fail auth
- Calling admin methods against a non-Enterprise-Grid workspace
- Not scoping bulk operations carefully — `AdminConversationsBulkDelete` is irreversible
- Assuming a full `admin.users.*` wrapper exists — the SDK does not currently expose user-provisioning admin endpoints as Go methods; use the REST API directly if you need those
- Forgetting `context.Context` as the first parameter on every admin call
- Confusing `AdminConversationsSetTeams` (move an existing channel) with `AdminConversationsCreate`'s `AdminConversationsCreateOptionTeamID` (set the team at creation time)

## Next Steps

- **Regular bot operations** → Use the `slack-web-api` skill
- **OAuth and token storage for the org-admin token itself** → Use the `slack-auth-security` skill
