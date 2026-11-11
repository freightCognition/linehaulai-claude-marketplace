---
name: cult-ui
description: This skill should be used when the user asks to "add a cult-ui component", "use cult-ui", "install <component> from cult ui", "find a cult-ui component for X", "what cult-ui components are there", "build a hero/pricing section/form with cult-ui", or names any Cult UI component (Dynamic Island, Texture Button, Halo Select, Prompt Composer, Border Beam Card, Hero Dithering, Text Animate, and so on). Also applies to animated shadcn/ui registry components, motion-rich React UI, and migrating hand-rolled components to cult-ui equivalents. Provides a complete catalog of all 134 components with docs links, install names and dependencies, plus the fetch-then-install workflow.
---

# Cult UI

Cult UI (https://www.cult-ui.com, source https://github.com/nolly-studio/cult-ui) is a shadcn/ui **registry**, not an npm package. Each component's source is copied into the project by the shadcn CLI and becomes owned code under `components/ui/`. Components use React, Tailwind CSS v4, shadcn theme tokens, and usually `motion` for animation.

## Core rule: look up, read the docs, then install

Never recreate a cult-ui component from memory, and never guess its props. For every component:

1. **Find it** in `references/components.md`. The catalog covers all 134 documented components, grouped by category, with the docs URL, markdown docs URL, install name, npm dependencies and shadcn dependencies. Search it with Grep instead of reading the whole file:
   - by name or slug: `Grep -i "dynamic island" references/components.md`
   - by need: `Grep -i "dropzone\|upload" references/components.md`
   - a whole category: `Grep -n "^## " references/components.md`, then read that section.
2. **Read its docs** by fetching the markdown URL (`https://www.cult-ui.com/docs/components/<slug>.md`). The `.md` page holds the description, a full demo, the API/props tables and the source, without the site chrome. Prefer it over the HTML page. Use WebFetch, or `curl -sL <url>` when the raw text is needed (for example, to copy source exactly). If WebFetch fails, use Firecrawl scrape on the same URL.
3. **Install it** with the shadcn CLI using the **install name** from the catalog:
   ```bash
   npx shadcn@latest add @cult-ui/<install-name>
   ```
   Use the project's own runner (`bunx`, `pnpm dlx`) when it has a lockfile for one.
4. **Adapt it** to the project (see "Fitting a component into a project" below).

### Doc slug vs install name

The docs slug and the registry install name usually match, but not always. The catalog shows both and flags each mismatch with a `note:`. Known cases:

| Docs slug | Install name |
| --- | --- |
| `bg-animated-fractal-grid` | `bg-animated-fractal-dot-grid` |
| `hero-color-panels` | `hero-color-panel` |

Installing the docs slug in these cases returns a 404.

### Deprecated aliases

The `animated-*` registry items (`animated-button`, `animated-card`, `animated-select`, and others) are deprecated aliases for the **Halo** kit (`halo-button`, `halo-card`, `halo-select`, ...). Always install the `halo-*` name. The catalog's last section, "Registry Items Without a Docs Page", lists every alias and the undocumented primitives (`base-select`, `base-tooltip`, `bg-animated-gradient`).

## Choosing a component

When the user describes a need rather than a name ("an animated pricing card", "a fancy file upload"), search the catalog by keyword and category, shortlist two to four candidates, and compare their one-line summaries and dependencies. Fetch the `.md` docs of the leading candidate before recommending it. Point out dependency weight when it matters: shader components pull in `@paper-design/shaders-react` (WebGL), the Halo kit and newer form controls use `@base-ui/react`, and the globe uses `cobe`.

Catalog categories: Device & Product Mockups, Heroes & Landing Sections, Illustrations & SVG, AI & Agent UI, Text & Typography, Buttons, Cards, Forms & Inputs, Navigation/Overlays & Layout, Media/Video & Social, Backgrounds/Shaders & Effects, Data/Charts & Code.

## Prerequisites in the target project

Installing needs what `npx shadcn@latest init` creates: `components.json`, the `cn` helper in `lib/utils.ts`, an `@/` import alias, and shadcn theme tokens in global CSS. Check for `components.json` first. If it is missing, ask before running `init`, because init edits config and global CSS. `references/setup.md` covers init per framework, manual installation without the CLI, pinning the registry in `components.json`, the shadcn MCP server, and troubleshooting.

## Fitting a component into a project

The installed file is owned code. After installing:

- **Theme tokens.** Components read `--card`, `--border`, `--input`, `--muted`, `--muted-foreground`, `--foreground`, `--background`, `--ring`, `--accent`, `--destructive`, `--chart-1..5` and `--radius`. If the project has its own design-token system or rules (check its CLAUDE.md/AGENTS.md), map those tokens onto the component and remove stock hex values and gradients the rules forbid. The Halo kit and Prompt Composer have hardcoded `linear-gradient(...)` rims, edited in the component file. Border Beam colors come from the `colorVariant`/`theme` props. Component-specific CSS variables (Organic Button, Illustration Globe Vercel, Tabs Illustration Vercel) are listed in `references/setup.md`.
- **Dark mode.** Styles switch on a `.dark` ancestor (`@custom-variant dark (&:is(.dark *))`). Globe, Gradient Button Group and Shader Lens Blur read `next-themes`. In a light-only or non-Next project, replace that hook with a constant or the project's theme source.
- **Non-Next.js frameworks** (Astro, Vite, Remix): cult-ui targets Next.js. Replace `next/image` and `next/link` imports with `<img>`/`<a>` or the framework's equivalents (Dither Image wraps `next/image`). `"use client"` is harmless outside Next. In Astro, render the component inside a React island with a `client:*` directive, because every animated component needs the browser.
- **Providers.** Compound components need their provider around the parts, for example `DynamicIslandProvider` around `DynamicIsland`. The `.md` docs show the required tree.
- **Motion and accessibility.** Animated components use `motion`. Respect the project's reduced-motion policy, keep focus rings (`--ring`), and verify contrast after retokening.
- **Updating.** `npx shadcn@latest add @cult-ui/<name> --overwrite` replaces the file with upstream. Diff it first, because local retokening is lost.

## Other machine-readable sources

| Source | Use |
| --- | --- |
| `https://www.cult-ui.com/llms.txt` | Live index of every component and guide page; check here when a component is not in the catalog (it may be new) |
| `https://www.cult-ui.com/llms-full.txt` | Every docs page with source in one large file; grep it rather than loading it whole |
| `https://www.cult-ui.com/r/registry.json` | Registry index: install names, `dependencies`, `registryDependencies` |
| `https://www.cult-ui.com/r/<install-name>.json` | One component's full source files and dependency lists |
| `npx shadcn@latest search @cult-ui --query <q>` / `npx shadcn@latest view @cult-ui/<name>` | Terminal search and preview |

## Keeping the catalog current

`references/components.md` is generated. To refresh it after cult-ui ships new components, run:

```bash
python3 scripts/sync_catalog.py
```

It fetches `llms.txt` and `registry.json`, rebuilds the catalog, and exits with an error naming any documented component that has no matching registry item. When that happens, add the slug-to-install-name pair to `ALIASES` in the script. Tests: `cd scripts && python3 -m unittest test_sync_catalog`.

## Additional resources

- **`references/components.md`**: the full catalog of 134 components, plus guide pages and undocumented registry items.
- **`references/setup.md`**: project setup, manual install, theming tokens and per-component CSS variables, the MCP server, troubleshooting.
- **`scripts/sync_catalog.py`**: catalog generator, with tests in `test_sync_catalog.py`.
- Slash commands from this plugin: `/cult-ui:find <need>` to pick a component, and `/cult-ui:add <component...>` to install and adapt one.
