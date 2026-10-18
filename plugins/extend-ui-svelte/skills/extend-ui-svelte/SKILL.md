---
name: extend-ui-svelte
description: This skill should be used when the user asks to "install extend-ui-svelte", "add an extend-ui component", "set up the PDF worker", "use extend-ui-svelte in SvelteKit", "fix SSR errors with the PDF viewer", "wire dark mode into extend-ui components", "pass isDark to the viewer", "configure Tailwind for extend-ui-svelte", "which engine does this component need", or mentions extend-ui-svelte, Extend UI Svelte, or the Svelte port of extend-hq/ui. It is the hub skill: what the library is, how to install it (copy-in registry or npm package), which engine dependencies each component pulls in, the shared dark-mode, cn, virtual-list and SSR contracts, and common pitfalls. Component-specific APIs live in the sibling skills extend-ui-viewers, extend-ui-editors, extend-ui-files-primitives and extend-ui-extraction.
---

# extend-ui-svelte (hub)

extend-ui-svelte is a Svelte 5 (runes) port of [extend-hq/ui](https://github.com/extend-hq/ui), MIT licensed, for document-heavy apps. Source: `github.com/fakebizprez/extend-ui-svelte`. Docs: `https://extend-ui-svelte.linehaul.ai`. npm: `extend-ui-svelte` (peer dep `svelte ^5.0.0`).

Use this skill for setup and cross-cutting rules. For a component's props and events, load the sibling skill named in the table.

## Component map

| Registry name | Exports | What it is | Sibling skill |
|---|---|---|---|
| `pdf-viewer` | `PdfViewer`, `PDFViewer` | Virtualized PDF.js pages, toolbar, zoom, rotate, page overlay snippet, download | extend-ui-viewers |
| `docx-viewer` | `DocxViewer`, `DocxViewerPreview` | Word rendering via docx-preview with thumbnail rail | extend-ui-viewers |
| `xlsx-viewer` | `XlsxViewer`, `XlsxViewerPreview`, `WorkbookSheetTabs` | SheetJS workbook, sheet tabs, virtual rows | extend-ui-viewers |
| `pptx-viewer` | `PptxViewer`, `PptxViewerPreview`, `PptxSlide` | Virtualized slide list via pptx-browser | extend-ui-viewers |
| `csv-tsv-viewer` | `CsvTsvViewer`, `CsvViewer`, `parseDelimitedText` | papaparse plus virtual table and search | extend-ui-viewers |
| `document-viewer-sidebar` | `DocumentViewerThumbnailSidebar`, `DocumentViewerSidebarSkeleton`, `useInlineThumbnailSidebar`, `useElementWidth` | Thumbnail rail that sits inline or overlays | extend-ui-viewers |
| `pdf-editor` | `PdfEditor`, `PDFEditor` | Reorder, rotate, delete pages; save with pdf-lib | extend-ui-editors |
| `docx-editor` | `DocxEditor`, `DocxEditorPreview` | In-browser Word editing, export to .docx | extend-ui-editors |
| `xlsx-editor` | `XlsxEditor`, `XlsxEditorPreview` | Editable cells, formulas, styling, export | extend-ui-editors |
| `e-signature` | `ESignature`, `ESignatureBlock` | Draw with signature_pad, stamp into a PDF with pdf-lib | extend-ui-editors |
| `file-upload` | `FileUpload` | Drop zone and file input with validation | extend-ui-files-primitives |
| `file-thumbnail` | `FileThumbnail` | File preview tile, PDF first page via the engine | extend-ui-files-primitives |
| `file-system` | `FileSystem` | Folder and file tree with selection | extend-ui-files-primitives |
| `group` | `Group`, `GroupText`, `GroupSeparator` (+ `ButtonGroup*` aliases) | Joins controls into one unit | extend-ui-files-primitives |
| `color-picker` | `ColorPicker`, `ColorPickerPanel` | Color selector | extend-ui-files-primitives |
| `toggle` | `Toggle`, `ToggleGroup`, `ToggleGroupItem` | Pressed-state button and group | extend-ui-files-primitives |
| `schema-builder` | `SchemaBuilder`, `SchemaBuilderPanel`, `SchemaJsonView` | Visual extraction-schema editor | extend-ui-extraction |
| `document-splits` | `DocumentSplits` + split helpers | Split a PDF into labeled page groups (native DnD) | extend-ui-extraction |
| `layout-blocks` | `LayoutBlocks`, `OcrBlocksPanel` | Virtualized OCR/layout block list with sanitized markdown | extend-ui-extraction |
| `bounding-box-citations` | `BoundingBoxCitations`, `HumanReviewBlock`, `HumanReviewPanel`, `HumanReviewHighlight`, `JsonDiffView`, `JsonCodeView` | Human review panel plus PDF with cited boxes | extend-ui-extraction |

Shared registry items (pulled in automatically as dependencies): `dark-mode`, `utils`, `virtual-list`, `engines`.

## Install

Pick one path. Full detail, including the dependency closure per component, is in `references/installation.md`.

1. **npm package** (simplest, all components). Install with the project's package manager, for example `bun add extend-ui-svelte` or `npm i extend-ui-svelte`. It brings every engine as a regular dependency. Import from the per-component subpath:
   ```ts
   import { PdfViewer } from 'extend-ui-svelte/components/pdf-viewer';
   ```
   The root (`extend-ui-svelte`) also re-exports every component plus `VirtualList`, `computeWindow`, `DEFAULT_OVERSCAN`, `resolveIsDark`, `toggleIsDark`, `DEFAULT_IS_DARK` and the `DarkModeProps` type. Only `.` and `./components/*` are exported; engines and `utils` are not reachable from the package.
2. **Copy-in registry** (shadcn-svelte style, editable source). The documented command is `npx shadcn-svelte add <registry-url>/<name>`, but no registry URL is published yet (`extend-ui-svelte.linehaul.ai/r/*.json` returns 404). Until it is, copy files listed in `registry.json` from `raw.githubusercontent.com/fakebizprez/extend-ui-svelte/main/<path>` and keep the `src/lib/` folder layout, because components import shared code with relative paths like `../../engines/pdf/index.js` and `../../dark-mode.js`.

To install a component interactively, run `/extend-ui-svelte:add-component <name>`.

## Engine dependencies

The `engines` registry item bundles all four engine wrappers, so any component that depends on it needs all four engine packages installed: `pdfjs-dist@^6.4.299`, `docx-preview@^0.4.1`, `pptx-browser@^4.1.5`, and SheetJS `xlsx` from `https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` (never npm's `xlsx@0.18.5`, which has known advisories). Component-specific extras:

- `pdf-viewer`, `pdf-editor`, `bounding-box-citations`: `pdf-lib@^1.17.1`
- `e-signature`: `pdf-lib@^1.17.1`, `signature_pad@^5.1.4`
- `docx-editor`: `jszip@^3.10.2`
- `csv-tsv-viewer`: `papaparse@^5.7.0` only (no engines)
- `layout-blocks`: `marked@^18.1.0`, `hast-util-sanitize@^5.0.2`, `hast-util-from-html@^2.0.3`, `hast-util-to-html@^9.0.5`
- `file-system`, `schema-builder`, `document-viewer-sidebar`, `group`, `color-picker`, `toggle`: no npm deps

## Cross-cutting rules

Apply these whenever writing code against the library.

- **Bundler must be Vite.** The PDF engine imports `pdfjs-dist/build/pdf.worker.mjs?url`. SvelteKit with Vite handles it; other bundlers need an equivalent `?url` loader. The worker is version-locked to the installed `pdfjs-dist` automatically, so no worker setup is needed by default. To serve the worker from elsewhere, call `setPdfWorkerSrc(url)` from the copied `engines/pdf/index.ts` (copy-in only; the npm package does not export it). See `references/ssr-and-engines.md`.
- **SSR is safe by default.** Components load engines with dynamic `import()` inside `onMount` or `$effect`, which never run on the server. Do not add `ssr = false` just to use a viewer. Import engine modules directly only in client code (inside `onMount`, an event handler, or behind `browser` from `$app/environment`), never in `+page.server.ts` or `+server.ts`.
- **Dark mode is parent-controlled.** Hold `let isDark = $state(false)` in the parent, pass `isDark`, and update it from `onIsDarkChange`. Components only add a `dark` class to their own root. `DocxViewer`, `XlsxViewer`, `DocxEditor` and `XlsxEditor` declare `isDark` and `onIsDarkChange` as required props and render their own theme switch, so always pass both to them. See `references/dark-mode-and-theming.md`.
- **Use `$state.raw` for parsed documents.** Workbooks, parsed CSV tables, page lists, and byte buffers must not be deep-proxied. Reassign instead of mutating.
- **Controlled values stay controlled.** Pass value plus callback (`splits` + `onSplitsChange`, `schema` + `onSchemaChange`, ToggleGroup `value` + `onValueChange`, ColorPicker `value` + `onChange`). Use `bind:` only on props declared `$bindable`: `values` and `activeFieldKey` on `BoundingBoxCitations`, `values` on `HumanReviewPanel`, `selectedPath` on `FileSystem`, and `positionX`, `positionY`, `signatureWidth`, `signatureHeight`, `scale` on `ESignature`.
- **Snippets replace React render props.** For example `pageOverlay` and `toolbarActions` on `PdfViewer` are snippets.
- **`class` and `className` are both accepted** on most components and merged.
- **Give viewers a height.** Virtualized components take a numeric `height` in px (for example `PdfViewer` `height`, `CsvTsvViewer` `height` defaults to 560). See `references/virtual-list.md` for using `VirtualList` directly.

## Styling

Viewers, editors and extraction components use scoped CSS and need no Tailwind. Only `group`, `toggle` and `color-picker` use Tailwind v4 utilities and shadcn-style theme tokens (`--background`, `--foreground`, `--muted`, `--border`, ...). For those three, set up Tailwind v4, define the tokens, add `@custom-variant dark (&:where(.dark, .dark *));`, and with the npm package add an `@source` line pointing at `node_modules/extend-ui-svelte/dist`. The full token block is in `references/dark-mode-and-theming.md`. The shipped `cn` (in `utils.ts`) only joins truthy class strings; it does not run tailwind-merge, so conflicting utilities are not deduplicated.

## Minimal example

```svelte
<script lang="ts">
	import { PdfViewer } from 'extend-ui-svelte/components/pdf-viewer';

	let isDark = $state(false);
</script>

<PdfViewer
	src="/files/contract.pdf"
	fileName="contract"
	defaultZoom="fit-width"
	height={720}
	{isDark}
	onIsDarkChange={(value) => (isDark = value)}
	onDocumentLoadSuccess={(numPages) => console.log(numPages)}
/>
```

## Pitfalls

- Installing `xlsx` from npm instead of the SheetJS CDN tarball pulls the vulnerable 0.18.5 line.
- Moving copied files out of the `src/lib/{components,engines,virtual-list}` layout breaks the relative imports.
- Importing engines from the npm package (`extend-ui-svelte/engines/...` or `/dist/...`) fails: the exports map blocks it. Copy the engine in or use the components.
- Omitting `onIsDarkChange` on the DOCX/XLSX viewers and editors is a type error, since both props are required there.
- Primitives render unstyled if Tailwind does not scan the library files or the theme tokens are missing.
- `migration-react-to-svelte.md` lists `widthClassName` and `closedInlineClassName` on `DocumentViewerThumbnailSidebar`; the source dropped them. Trust the component source over that note.
- In the library's own Vitest runs, an "EnvironmentTeardownError" from `pdf.worker.mjs` can appear when a test ends before the engine import resolves. Fix it the way the repo does: import the PDF engine module once in the Vitest client setup file so later imports resolve from cache.

## References

- `references/installation.md`: both install paths, the dependency closure per component, the copy procedure, and the package manager matrix.
- `references/ssr-and-engines.md`: engine APIs (pdf, docx, xlsx, pptx), worker setup, SvelteKit SSR patterns, `$state.raw`.
- `references/dark-mode-and-theming.md`: the `DarkModeProps` contract, helpers, Tailwind v4 token block.
- `references/virtual-list.md`: `VirtualList` props and the windowing helpers.
