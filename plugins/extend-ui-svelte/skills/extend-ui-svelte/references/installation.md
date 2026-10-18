# Installation

Two supported paths. Both target Svelte 5 with Vite (SvelteKit is the tested host).

## Path A: npm package

```sh
bun add extend-ui-svelte      # or: npm i / pnpm add / yarn add
```

- Published name `extend-ui-svelte` (latest `0.1.0` at time of writing), MIT, peer dependency `svelte ^5.0.0`.
- Every engine is a regular `dependencies` entry, so one install brings `pdfjs-dist`, `docx-preview`, `xlsx` (SheetJS CDN tarball), `pptx-browser`, `pdf-lib`, `signature_pad`, `papaparse`, `jszip`, `marked`, and the three `hast-util-*` packages. Unused engines are not bundled because components load them with dynamic `import()`.
- Exports map (only these two entries resolve):

  | Specifier | Resolves to |
  |---|---|
  | `extend-ui-svelte` | `dist/index.js` |
  | `extend-ui-svelte/components/<name>` | `dist/components/<name>/index.js` |

  `<name>` is the registry folder name, for example `pdf-viewer`, `xlsx-editor`, `bounding-box-citations`.
- Prefer the subpath import. It exposes every helper that component's `index.ts` exports (for example `createInitialSplits` from `document-splits`, zoom helpers from `pdf-viewer`). The root only re-exports the components, a few types, the dark-mode helpers, `VirtualList`, `computeWindow`, `DEFAULT_OVERSCAN`, `CsvTsvViewerDefault`, and `parseDelimitedText`.
- Not reachable from the package: `engines/*` (so no `setPdfWorkerSrc`, `createPdfEngine`, `renderDocx`, `loadWorkbookFromBytes`, `loadDeck`) and `utils` (`cn`). If an app needs those, use Path B for the `engines` or `utils` item.

```svelte
<script lang="ts">
	import { CsvTsvViewer } from 'extend-ui-svelte/components/csv-tsv-viewer';
	let isDark = $state(false);
	const data = 'name,qty\nbolts,40\nnuts,12';
</script>

<CsvTsvViewer {data} search height={400} {isDark} />
```

## Path B: copy-in registry (shadcn-svelte style)

`registry.json` in the repo root is a shadcn-svelte registry (`$schema: https://shadcn-svelte.com/schema/registry.json`, name `extend-ui-svelte`). The docs site documents:

```sh
npx shadcn-svelte add <registry-url>/<name>
```

No registry URL is published yet: `https://extend-ui-svelte.linehaul.ai/r/<name>.json` and `/registry.json` both returned 404 on 2026-10-18, and the repo has no built `static/r/` output. Check those URLs again before falling back. Until they exist, install by copying files:

1. Fetch `https://raw.githubusercontent.com/fakebizprez/extend-ui-svelte/main/registry.json`.
2. Find the item by `name`. Walk `registryDependencies` recursively and collect every item (closure table below).
3. For every `files[].path` (all start with `src/lib/`), download `https://raw.githubusercontent.com/fakebizprez/extend-ui-svelte/main/<path>` and write it under one base folder in the app, keeping everything after `src/lib/`. Recommended base: `src/lib/extend-ui/`. Example: `src/lib/components/pdf-viewer/PdfViewer.svelte` becomes `src/lib/extend-ui/components/pdf-viewer/PdfViewer.svelte`, and `src/lib/engines/pdf/pdf-engine.ts` becomes `src/lib/extend-ui/engines/pdf/pdf-engine.ts`.
4. Keep that structure exactly. Components import siblings with relative paths (`../../engines/pdf/index.js`, `../../virtual-list/index.js`, `../../dark-mode.js`, `../../utils.js`), with `.js` extensions written for strict ESM.
5. Install every npm entry in the closure's `dependencies` arrays.
6. Import from the copy: `import { PdfViewer } from '$lib/extend-ui/components/pdf-viewer/index.js';`

Each file starts with an MIT attribution header crediting extend-hq/ui. Keep it.

## Dependency closure per component

`engines` npm deps: `pdfjs-dist@^6.4.299`, `docx-preview@^0.4.1`, `pptx-browser@^4.1.5`, `xlsx@https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz`.

| Component | Registry items pulled in | npm packages to install |
|---|---|---|
| `pdf-viewer` | engines, virtual-list | engines + `pdf-lib@^1.17.1` |
| `docx-viewer` | engines, virtual-list | engines |
| `xlsx-viewer` | dark-mode, engines, virtual-list | engines |
| `pptx-viewer` | engines, virtual-list | engines |
| `csv-tsv-viewer` | (none) | `papaparse@^5.7.0` |
| `document-viewer-sidebar` | dark-mode | (none) |
| `pdf-editor` | pdf-viewer, engines, virtual-list | engines + `pdf-lib@^1.17.1` |
| `docx-editor` | dark-mode, engines | engines + `jszip@^3.10.2` |
| `xlsx-editor` | xlsx-viewer, dark-mode, engines, virtual-list | engines |
| `e-signature` | engines | engines + `pdf-lib@^1.17.1`, `signature_pad@^5.1.4` |
| `file-upload` | file-thumbnail, engines | engines |
| `file-thumbnail` | engines | engines |
| `file-system` | dark-mode | (none) |
| `document-splits` | file-thumbnail, dark-mode, engines | engines |
| `schema-builder` | (none) | (none) |
| `layout-blocks` | dark-mode, virtual-list | `marked@^18.1.0`, `hast-util-sanitize@^5.0.2`, `hast-util-from-html@^2.0.3`, `hast-util-to-html@^9.0.5` |
| `bounding-box-citations` | pdf-viewer, utils, virtual-list, engines | engines + `pdf-lib@^1.17.1` |
| `group` | dark-mode, utils | (none) |
| `color-picker` | dark-mode, utils | (none) |
| `toggle` | group, dark-mode, utils | (none) |

The `engines` item ships all four wrappers together. There is no per-engine split, so a PDF-only app still installs `docx-preview`, `pptx-browser`, and `xlsx` to satisfy imports and type-checking.

## Package manager commands

Detect from the lockfile: `bun.lock` or `bun.lockb` means bun, `pnpm-lock.yaml` means pnpm, `yarn.lock` means yarn, `package-lock.json` means npm.

| Manager | Add | SheetJS |
|---|---|---|
| bun | `bun add <pkgs>` | `bun add https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` |
| npm | `npm i <pkgs>` | `npm i https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` |
| pnpm | `pnpm add <pkgs>` | `pnpm add https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` |
| yarn | `yarn add <pkgs>` | `yarn add xlsx@https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` |

Never install `xlsx` from the npm registry: npm's latest is 0.18.5, which has known prototype-pollution and ReDoS advisories.

## Tailwind and CSS

Only `group`, `toggle` and `color-picker` need Tailwind v4 (utility classes plus shadcn-style tokens). Every other component ships scoped `<style>` blocks with its own CSS custom properties (`--pdf-*`, `--xlsx-*`, `--hr-*`, `--splits-*`, ...) and works without Tailwind. Setup for the primitives is in `dark-mode-and-theming.md`.

## Verify the install

- `bunx svelte-check` (or the project's `check` script) passes with the new imports.
- Render the component on a page with `vite dev` and confirm the PDF, workbook, or deck loads. Engines only run in the browser, so a server render alone proves nothing.
