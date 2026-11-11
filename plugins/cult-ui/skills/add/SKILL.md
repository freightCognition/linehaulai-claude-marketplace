---
name: add
description: Install one or more Cult UI components into the current project with the shadcn CLI, after reading their docs, then adapt them to the project.
argument-hint: <component name(s), e.g. "dynamic island" or "halo-select halo-switch">
allowed-tools: Read, Edit, Grep, Glob, WebFetch, Bash
---

Install these Cult UI components into the current project: **$ARGUMENTS**

Follow the `cult-ui` skill's rules throughout. The catalog is at `${CLAUDE_PLUGIN_ROOT}/skills/cult-ui/references/components.md` (Glob `**/skills/cult-ui/references/components.md` if the path does not resolve). The setup guide is the `references/setup.md` file beside it.

## 1. Resolve names

For each requested component, Grep the catalog case-insensitively for its name or slug and take the **install name** (the `install @cult-ui/<name>` field).

- If there are several plausible matches, pick the exact name match. If none is exact, ask which one was meant.
- If an `animated-*` name is requested, install the matching `halo-*` component instead and say so; the `animated-*` items are deprecated aliases.
- If nothing matches, check `https://www.cult-ui.com/llms.txt` and `https://www.cult-ui.com/r/registry.json` for a newer component. If it is still missing, stop and report it, and suggest `/cult-ui:find`.
- If `$ARGUMENTS` is empty, ask which component to add.

## 2. Check the project

- Confirm `components.json` exists at the project root. If it is missing, stop and ask before running `npx shadcn@latest init`, because init rewrites config and global CSS.
- Read `components.json` for the `ui` alias, so the output path is known.
- Pick the runner from the lockfile: `bun.lock`/`bun.lockb` → `bunx`, `pnpm-lock.yaml` → `pnpm dlx`, `yarn.lock` → `yarn dlx`, otherwise `npx`.
- Read the project's CLAUDE.md/AGENTS.md for design-token, styling, motion or framework rules that the component must meet.

## 3. Read the docs before installing

Fetch `https://www.cult-ui.com/docs/components/<docs-slug>.md` for each component (WebFetch; `curl -sL` for raw text). Note the required provider wrappers, props, variants, the demo usage, and any Next.js-only imports.

## 4. Install

```bash
<runner> shadcn@latest add @cult-ui/<install-name> [@cult-ui/<another>]
```

- Never pass `--overwrite` unless the user asked for it. If the file already exists, show the diff and ask.
- If the namespace is unknown, retry by URL: `shadcn@latest add https://www.cult-ui.com/r/<install-name>.json`.
- Report the CLI's actual error output on failure, and use the troubleshooting table in `references/setup.md`.

## 5. Adapt

Read each file the CLI wrote, then:

- Retoken to the project's design system when it has one: replace hardcoded hex, gradients or radii that its rules forbid with the project's tokens or CSS variables.
- Outside Next.js, replace `next/image`/`next/link` imports and swap `next-themes` usage for the project's theme source. In Astro, hydrate the component as a React island with a `client:*` directive.
- Keep accessibility intact: focus rings, labels, keyboard handling and contrast.

## 6. Verify and report

- Run the project's type check or build, plus any lint and test gates its CLAUDE.md names, and report the real results.
- If the user asked for the component to be placed on a page, use the docs demo as the usage template.
- Finish with: the files added or changed, the npm packages installed, the adaptations made, and the gate results.
