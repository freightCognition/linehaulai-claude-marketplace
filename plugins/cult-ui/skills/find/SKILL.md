---
name: find
description: Recommend the best Cult UI components for a described need, with docs links and install commands.
argument-hint: <what you need, e.g. "animated pricing card" or "file upload">
allowed-tools: Read, Grep, Glob, WebFetch, Bash(curl:*)
---

Find the Cult UI components that best fit this request: **$ARGUMENTS**

This command is read-only. Do not install anything.

1. Locate the catalog at `${CLAUDE_PLUGIN_ROOT}/skills/cult-ui/references/components.md`. If that path does not resolve, Glob for `**/skills/cult-ui/references/components.md`.
2. If `$ARGUMENTS` is empty, list the catalog's categories with their counts (`Grep -n "^## "`) and ask what the user is building.
3. Otherwise, derive three to six keywords and synonyms from the request (e.g. "file upload" → upload, dropzone, file, drag), and Grep the catalog case-insensitively for each. Each entry spans three lines (name/links, summary, dependencies), so use `-A 2` to see the full entry. Also scan the matching category section.
4. If nothing matches, check the live index (`curl -sL https://www.cult-ui.com/llms.txt`), since the component may be newer than the catalog.
5. Shortlist the two to four best candidates. Fetch the `.md` docs of the top candidate with WebFetch to confirm it fits and to note its key props or variants.
6. Reply with a short ranked list. For each candidate give the name linked to its docs page, one line on why it fits, the install command `npx shadcn@latest add @cult-ui/<install-name>` (use the catalog's install name, which can differ from the docs slug), and any heavy dependencies (WebGL shaders, `@base-ui/react`, `cobe`). Put the top pick's key props after the list.
7. End by naming `/cult-ui:add <install-name>` as the next step for the top pick.
