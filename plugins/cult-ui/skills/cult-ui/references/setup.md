# Cult UI Setup, Theming and MCP

Condensed from the official guides: Installation (https://www.cult-ui.com/docs/installation.md), Manual Installation (https://www.cult-ui.com/docs/installation/manual.md), Theming (https://www.cult-ui.com/docs/theming.md), MCP Server (https://www.cult-ui.com/docs/mcp-server.md), and LLMs & Agents (https://www.cult-ui.com/docs/llms.md). Re-fetch those pages when something here looks out of date.

## 1. Project prerequisites

Cult UI needs what `shadcn init` creates:

- `components.json`
- the `cn` helper in `lib/utils.ts`
- an `@/` import alias
- shadcn theme tokens in global CSS

```bash
npx shadcn@latest init
```

To scaffold a new project, pass `-t` with `next`, `vite`, `start`, `react-router` or `astro`. The framework guides are at `/docs/installation/next.md` and `/docs/installation/vite.md`.

## 2. Adding components

```bash
npx shadcn@latest add @cult-ui/halo-button
npx shadcn@latest add @cult-ui/halo-card @cult-ui/halo-input @cult-ui/halo-switch   # several at once
npx shadcn@latest add https://www.cult-ui.com/r/halo-button.json                     # by URL, any CLI version
```

- The `@cult-ui` namespace is listed in the shadcn registry directory, so it needs no `components.json` edit with CLI 3.0 or later.
- The CLI writes `components/ui/<name>.tsx`, installs npm dependencies, and adds any shadcn components the item builds on (`registryDependencies`).
- Import from the path the CLI printed, e.g. `import { HaloButton } from "@/components/ui/halo-button"`.
- Search and preview: `npx shadcn@latest search @cult-ui --query card`, `npx shadcn@latest view @cult-ui/prompt-composer`.
- Update: `npx shadcn@latest add @cult-ui/<name> --overwrite`. This replaces local edits, so diff the file first.

### Pinning the registry

Pin the registry for a CLI older than 3.0, for environments that cannot reach the shadcn registry directory, for the MCP server, or to make the URL explicit:

```json
{
  "registries": {
    "@cult-ui": "https://www.cult-ui.com/r/{name}.json"
  }
}
```

## 3. Manual installation (no CLI)

1. Tailwind CSS v4, plus `tw-animate-css` for `animate-in`/exit classes:
   ```css
   @import "tailwindcss";
   @import "tw-animate-css";
   @custom-variant dark (&:is(.dark *));
   ```
2. Theme tokens for `:root` and `.dark`, mapped in `@theme inline` (see section 4).
3. The `cn` helper (`npm install clsx tailwind-merge`):
   ```ts
   import { clsx, type ClassValue } from "clsx"
   import { twMerge } from "tailwind-merge"
   export function cn(...inputs: ClassValue[]) {
     return twMerge(clsx(inputs))
   }
   ```
4. The `@/*` path alias in `tsconfig.json` (`"@/*": ["./src/*"]`, or `["./*"]` without `src`), and in the bundler if it ignores tsconfig paths.

Then for each component, read `https://www.cult-ui.com/r/<install-name>.json`. It lists `dependencies` (npm), `registryDependencies` (components it builds on) and the full source in `files[].content`. Install the deps, add the registry deps, and copy the source into `components/ui/<name>.tsx`, fixing import paths if the alias differs.

## 4. Theming

Components use the standard shadcn CSS variables, so the existing theme applies.

| Token | What it controls |
| --- | --- |
| `--card` | Surfaces of cards, Halo controls, frosted fills mixed from it |
| `--border`, `--input` | Hairline borders, input outlines, control tracks |
| `--muted`, `--muted-foreground` | Secondary surfaces, placeholders, captions, icons |
| `--foreground`, `--background` | Body text, page backgrounds |
| `--ring` | Focus rings on every interactive component |
| `--accent`, `--destructive` | Hover and error states |
| `--chart-1` … `--chart-5` | Globe marker and arc colors |
| `--radius` | Corner radius for components that follow the theme's rounding |

- **Dark mode**: a `.dark` ancestor class. Globe, Gradient Button Group and Shader Lens Blur also read `next-themes` for canvas colors.
- **Per-instance styling**: every component accepts `className`, merged last with `cn`, so passed classes win.
- **Component CSS variables** for colors that tokens do not cover:

  | Component | Variables |
  | --- | --- |
  | Organic Button | `--organic-surface`, `--organic-fg`, `--organic-duration` |
  | Illustration Globe Vercel | `--globe-bg`, `--globe-dot`, `--globe-wire`, `--globe-icon`, `--globe-error` |
  | Tabs Illustration Vercel | `--ga-bg`, `--ga-fg`, `--ga-surface`, `--ga-border`, other `--ga-*` |

  ```tsx
  <OrganicButton className="[--organic-fg:var(--primary-foreground)] [--organic-surface:var(--primary)]">
    Get started
  </OrganicButton>
  ```
- **Brand gradients**: the Halo kit and Prompt Composer rims are fixed `linear-gradient(...)` values in the component file, so edit them there. Border Beam components take colors from the `border-beam` package through the `colorVariant` and `theme` props.
- **Adding a token**: define it in `:root` and `.dark`, then expose it in `@theme inline { --color-x: var(--x); }`.

## 5. shadcn MCP server

This server lets an agent search the cult-ui registry, read examples, and run `shadcn add`. It only searches registries listed in `components.json`, so pin `@cult-ui` first (section 2).

```bash
npx shadcn@latest mcp init --client claude   # writes .mcp.json; restart Claude Code, check /mcp
```

Manual config:

```json
{ "mcpServers": { "shadcn": { "command": "npx", "args": ["shadcn@latest", "mcp"] } } }
```

Mention "cult-ui" in prompts so it searches the right registry. If it shows "No tools or prompts", run `npx clear-npx-cache` and restart the server.

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `@cult-ui` registry unknown | Use `npx shadcn@latest` (not an old global CLI); otherwise pin the registry in `components.json` |
| 404 on install | Wrong name: use the catalog's install name, not the docs slug (e.g. `hero-color-panel`) |
| `Cannot find module @/lib/utils` | Project not initialized: run `shadcn init` or do the manual setup |
| Renders unstyled / wrong colors | Theme tokens missing for `:root`/`.dark`, or Tailwind not scanning `components/` |
| Files land in the wrong folder | Check `aliases` in `components.json`; run the CLI in a terminal to see the full error |
| `next/image` or `next/link` errors outside Next.js | Replace with `<img>`/`<a>` or the framework's own components |
| Hydration or `window is not defined` errors | Render client-only (`"use client"` in Next; a `client:*` island in Astro) |

## 7. Agent rules (from cult-ui, for AGENTS.md/CLAUDE.md)

- Install with `npx shadcn@latest add @cult-ui/<name>`; never recreate components by hand.
- Find names in https://www.cult-ui.com/llms.txt; read `https://www.cult-ui.com/docs/components/<name>.md` before use.
- Installed source in `components/ui/` is owned code; edit it there.
- Style with theme tokens (`bg-background`, `text-foreground`, `ring-ring`), not hardcoded colors.
- Animated components use `motion`; respect `prefers-reduced-motion` unless project policy says otherwise.
