# Plugin Overview

## Architecture

### Skill Hierarchy

```
slack-client-fundamentals (Foundation)
    ↓
    ├─→ slack-web-api (Synchronous Operations, incl. Canvas/Calls/Assistant)
    ├─→ slack-realtime-events (Socket Mode + Events API)
    ├─→ slack-auth-security (OAuth + Token Management)
    └─→ slack-admin-api (Enterprise Grid Administration)
```

**Pattern**: Hybrid - Foundation skill with four parallel concern-based skills

### Design Rationale

- **Foundation First**: `slack-client-fundamentals` provides shared knowledge (client setup, retry config, testing, architecture decisions)
- **Parallel Concerns**: Four independent skills allow focused usage without loading unnecessary context
- **Admin Split Out**: `slack-admin-api` is separated from `slack-web-api` because it requires a different token type (org admin, not bot) and targets a different audience (workspace admins, not bot developers)
- **Progressive Disclosure**: Skills provide quick reference (~80-90 lines), references provide depth (~80-100 lines each)

## Coverage Map

### Web API (slack-web-api)

**Core Operations**:
- Messaging: PostMessage, UpdateMessage, DeleteMessage, threading, ephemeral
- Channels: Create, list, manage, invite, archive, metadata
- Users: GetUserInfo, list users, presence, profiles, direct messages
- Files: Upload, download, share, delete, multi-part uploads
- Block Kit: Sections, buttons, selects, images, modals, forms

**Reference Files** (9):
- web-api-messaging.md
- web-api-channels.md
- web-api-users.md
- web-api-files.md
- block-kit-integration.md
- pagination-patterns.md
- canvas-api.md
- calls-api.md
- assistant-api.md

### Real-time Events (slack-realtime-events)

**Socket Mode**:
- WebSocket-based event handling
- Behind-firewall support
- Automatic reconnection
- App-level token authentication

**Events API**:
- HTTP webhook events
- Request verification
- URL challenge handling
- Retry logic

**Event Types**:
- message, message_changed, message_deleted
- app_mention, reaction_added/removed
- channel_created/renamed/archived
- team_join, user_change
- Interactive components (buttons, modals, shortcuts)
- Slash commands

**Reference Files** (5):
- socket-mode-setup.md
- events-api-webhooks.md
- event-types.md
- interactive-components.md
- slash-commands.md

### Auth & Security (slack-auth-security)

**OAuth Features**:
- OAuth 2.0 authorization flow
- Bot vs user tokens
- Multi-workspace installations
- Token exchange and storage

**Security**:
- Request signature verification
- Token encryption
- Secrets management
- Rate limiting
- HTTPS enforcement

**Token Management**:
- Secure storage (database, secrets manager)
- Token rotation
- Token validation
- Workspace-specific tokens

**Reference Files** (5):
- oauth-flow.md
- token-management.md
- scopes-permissions.md
- manifest-api.md
- security-checklist.md

### Admin API (slack-admin-api)

**Enterprise Grid Administration**:
- Conversations: search, archive/unarchive, rename, delete, bulk archive/delete/move, restrict access, retention, EKM
- Roles: add/list/remove role assignments
- Teams: settings info, name, description, icon, default channels, discoverability

**Requirements**:
- Org-level admin/owner token (not a bot token)
- Enterprise Grid workspace

**Reference Files** (1):
- admin-api-reference.md

## When to Use Each Skill

### slack-client-fundamentals

**Trigger Questions**:
- "How do I initialize a Slack client?"
- "What's the difference between Web API and Socket Mode?"
- "How do I test my Slack bot?"
- "What project structure should I use?"

**Use Cases**:
- Starting a new Slack bot project
- Choosing between Web API, Socket Mode, Events API
- Setting up testing infrastructure
- Configuring the Slack client

### slack-web-api

**Trigger Questions**:
- "How do I send a message to Slack?"
- "How do I create a channel?"
- "How do I upload a file?"
- "How do I get user information?"
- "How do I use Block Kit?"

**Use Cases**:
- Sending notifications and alerts
- Managing channels and users
- File operations
- Creating rich, interactive messages
- Any synchronous API call

### slack-realtime-events

**Trigger Questions**:
- "How do I handle Slack events?"
- "How do I use Socket Mode?"
- "How do I handle button clicks?"
- "How do I create a slash command?"
- "How do I respond to mentions?"

**Use Cases**:
- Building interactive bots
- Responding to user actions
- Event-driven applications
- Real-time notifications
- Apps behind firewalls (Socket Mode)

### slack-auth-security

**Trigger Questions**:
- "How do I implement OAuth for my app?"
- "How do I store Slack tokens securely?"
- "How do I support multiple workspaces?"
- "What scopes do I need?"
- "How do I rotate tokens?"

**Use Cases**:
- Distributing apps to multiple workspaces
- Implementing secure token storage
- OAuth flow implementation
- Production security hardening
- Multi-tenant applications

### slack-admin-api

**Trigger Questions**:
- "How do I search conversations across the whole org?"
- "How do I assign an admin role to a user?"
- "How do I bulk-archive or move channels between teams?"
- "How do I change a workspace's discoverability setting?"
- "How do I restrict a channel to specific groups?"

**Use Cases**:
- Internal tooling for Enterprise Grid org admins
- Bulk channel lifecycle management
- Role assignment automation
- Workspace/team settings management

## Reference Documentation

### Organization

References are organized by **concern** rather than skill:

```
references/
├── Core Setup (2 files)
├── Web API (9 files)
├── Admin API (1 file)
├── Real-time Events (5 files)
└── Auth & Security (5 files)

Total: 22 reference files
```

### Progressive Disclosure Strategy

**Level 1: Skill Description** (50 chars)
- Shown in skill list
- Includes trigger phrases

**Level 2: SKILL.md Content** (80-90 lines)
- Quick reference with code snippets
- Common use cases
- Links to detailed references

**Level 3: Reference Files** (80-100 lines each)
- Comprehensive guides
- Production-ready patterns
- Complete code examples
- Edge cases and error handling

## Integration with Other Plugins

### golang-orchestrator

**Architectural Alignment**:
- Both follow hierarchical foundation pattern
- `slack-client-fundamentals` can reference `effective-go` for Go best practices
- Testing patterns align with golang-orchestrator guidance
- Project structure recommendations compatible

**Cross-References**:
- Use `effective-go` for Go idioms and conventions
- Use `backend-service-patterns` for service architecture
- Combine for complete Go backend with Slack integration

### block-kit (if available)

**Relationship**:
- slack-go-sdk includes basic Block Kit guidance
- `references/block-kit-integration.md` covers common patterns
- block-kit plugin provides advanced layouts and complex forms
- Optional enhancement, not required

**Standalone Completeness**:
- Plugin works without block-kit plugin
- Covers 80% of Block Kit use cases
- References block-kit for advanced scenarios

## File Statistics

- **Total Files**: 32
- **Skills**: 5 (~460 lines total)
- **References**: 22 (~2,000 lines total)
- **Documentation**: 4 (~390 lines)
- **Plugin Manifest**: 1

**Total Lines**: ~2,850 (excluding code examples, approximate)

## Design Decisions

### 1. Hybrid Pattern (Foundation + Parallel)
- **Why**: Slack SDK has three independent domains (sync API, async events, auth)
- **Benefit**: Developers can target specific use cases without loading unnecessary context

### 2. Progressive Disclosure
- **Why**: Balance immediate value with comprehensive coverage
- **Benefit**: Quick answers in skills, deep dives in references

### 3. Concern-Based References
- **Why**: Multiple skills may reference same guide
- **Benefit**: No duplication, easier to maintain

### 4. Standalone Completeness
- **Why**: Plugin should be useful without dependencies
- **Benefit**: Works immediately after installation

### 5. Inline Examples Only
- **Why**: Go SDK examples most valuable with context
- **Benefit**: Simpler navigation, no context switching

## Success Metrics

**Coverage**:
- ✅ Web API (messaging, channels, users, files, Block Kit)
- ✅ Canvas, Calls, and Assistant thread APIs
- ✅ Socket Mode (WebSocket events)
- ✅ Events API (HTTP webhooks)
- ✅ OAuth (multi-workspace, token management)
- ✅ Enterprise Grid Admin API (conversations, roles, teams)
- ✅ Security (verification, encryption, best practices)
- ✅ Built-in retry configuration and `slacktest` mock server

**Quality**:
- ✅ Production-ready code examples
- ✅ Error handling patterns
- ✅ Testing strategies
- ✅ Security checklist
- ✅ Performance optimization

**Usability**:
- ✅ Clear skill descriptions with trigger phrases
- ✅ Quick start guide for beginners
- ✅ Progressive disclosure for all levels
- ✅ Integration guidance for related plugins
