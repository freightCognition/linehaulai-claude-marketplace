# cult-ui

A Claude Code plugin for [Cult UI](https://www.cult-ui.com/docs/components), a shadcn/ui registry of motion-rich React components.

## What it provides

| Component | Purpose |
| --- | --- |
| `cult-ui` skill | Loads automatically when you mention cult-ui or one of its components. Holds the fetch-docs-then-install workflow, the rules for fitting components into a project (tokens, dark mode, non-Next frameworks), and a full catalog. |
| `/cult-ui:find <need>` | Recommends the best-fitting components for a described need, with docs links and install commands. Read-only. |
| `/cult-ui:add <component...>` | Resolves names, reads each component's docs, installs with the shadcn CLI, adapts the result to the project, and runs its gates. |

The catalog (`skills/cult-ui/references/components.md`) lists all 134 documented components in 12 categories. Each entry has:

- the docs page and the markdown docs URL (`.md`, best for WebFetch)
- the shadcn install name, flagged where it differs from the docs slug
- npm and shadcn dependencies

It also lists the guide pages and the registry items that have no docs page, including the deprecated `animated-*` aliases for the Halo kit.

## Install

```
/plugin marketplace add linehaul-ai/linehaulai-claude-marketplace
/plugin install cult-ui@linehaulai-claude-marketplace
```

Target projects need shadcn/ui set up (`npx shadcn@latest init`). See `skills/cult-ui/references/setup.md`.

## Refreshing the catalog

The catalog is generated from `https://www.cult-ui.com/llms.txt` and `https://www.cult-ui.com/r/registry.json`:

```bash
cd plugins/cult-ui/skills/cult-ui/scripts
python3 sync_catalog.py               # rewrites ../references/components.md
python3 -m unittest test_sync_catalog # tests
```

The script fails loudly if a documented component has no registry item, which usually means the docs slug and install name have diverged. Add the pair to `ALIASES` in the script and re-run it.

It needs only the Python 3.9+ standard library.
