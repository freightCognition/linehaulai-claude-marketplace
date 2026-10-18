# extend-ui-svelte

Claude Code guidance for building document-heavy Svelte 5 apps with
[extend-ui-svelte](https://github.com/extend-hq/ui), the Svelte 5 port of Extend UI (MIT).

## Install

```shell
/plugin marketplace add freightCognition/linehaulai-claude-marketplace
/plugin install extend-ui-svelte@linehaulai-claude-marketplace
```

## Skills

| Skill | Covers |
|-------|--------|
| `extend-ui-svelte` | Installation (registry and npm), engine dependencies, PDF worker, SvelteKit SSR, dark mode contract, virtual list |
| `extend-ui-viewers` | PDF, DOCX, XLSX, PPTX, and CSV/TSV viewers, document viewer sidebar |
| `extend-ui-editors` | PDF, DOCX, and XLSX editors, e-signature |
| `extend-ui-files-primitives` | File upload, file thumbnail, file system, group, color picker, toggle |
| `extend-ui-extraction` | Schema builder, document splits, layout blocks, bounding-box citations |

Skills load automatically when you ask for something they cover, such as
"show this PDF with citations next to it" or "add drag-and-drop upload".

## Commands

- `/extend-ui-svelte:add-component <component-name>` adds a component to the current
  project, installs the engine it needs, and drops in a minimal usage example.

## License

MIT. Upstream credit: `extend-hq/ui`.
