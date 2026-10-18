---
name: extend-ui-viewers
description: This skill should be used when the user asks to display a PDF, render a DOCX, XLSX, PPTX, CSV, or TSV file, preview a Word document, spreadsheet, or slide deck in Svelte, build a document viewer or "open any file" viewer, add a page overlay or highlights on top of PDF pages, or add a thumbnail sidebar to a viewer using extend-ui-svelte (PdfViewer, DocxViewer, XlsxViewer, PptxViewer, CsvTsvViewer, DocumentViewerThumbnailSidebar).
---

# extend-ui-svelte document viewers

Read-only viewers for the Svelte 5 port of Extend UI. For install, SSR, dark mode basics, engines, and `VirtualList`, see the core skill at `../extend-ui-svelte/SKILL.md`. This skill covers choosing and wiring the viewers.

## Imports

Import from the package root or from the per-component entry. Both are in the package `exports` map:

```ts
import { PdfViewer, DocxViewer, XlsxViewer, PptxViewer, CsvTsvViewer } from 'extend-ui-svelte';
import { PdfViewer, type PdfViewerProps } from 'extend-ui-svelte/components/pdf-viewer';
```

If the components were copied in through the shadcn-svelte style registry, import the same names from `$lib/components/<name>/index.js` (for example `$lib/components/pdf-viewer/index.js`). The registry entries depend on `engines`, `virtual-list`, and sometimes `dark-mode`, so those land under `$lib/engines`, `$lib/virtual-list`, and `$lib/dark-mode.ts`.

Some helpers exist only on the per-component entry: `PptxSlide`, the DOCX zoom helpers and `DocxViewerProps`, `XlsxViewerProps`, `PptxViewerProps`, and `INLINE_THUMBNAIL_SIDEBAR_MIN_WIDTH`.

Each component is also exported under its upstream React name: `PDFViewer`, `DocxViewerPreview`, `XlsxViewerPreview`, `PptxViewerPreview`, `CsvViewer`.

## Pick a viewer

| File type | Extensions / MIME | Component | Source prop |
|---|---|---|---|
| PDF | `.pdf`, `application/pdf` | `PdfViewer` | `src: string` (URL or object URL) |
| Word | `.docx`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `DocxViewer` | `src: string` |
| Excel | `.xlsx` (anything SheetJS reads) | `XlsxViewer` | `src: string` or `data: ArrayBuffer \| Uint8Array` |
| PowerPoint | `.pptx`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `PptxViewer` | `src: string` |
| CSV / TSV | `.csv`, `.tsv`, `text/csv`, `text/tab-separated-values` | `CsvTsvViewer` | `data: string` (raw text) |

Inputs:
- None of the viewers takes a `File` directly. For a `File` or `Blob`, pass `URL.createObjectURL(file)` as `src`, and revoke the URL when the file changes. Pass `await file.arrayBuffer()` as `data` to `XlsxViewer`, and `await file.text()` as `data` to `CsvTsvViewer`.
- Legacy `.doc` and `.ppt` cannot be rendered. `DocxViewer`'s upload input accepts `.doc` files, but docx-preview fails on them.
- `XlsxViewer` and `DocxViewer` **require** `isDark` and `onIsDarkChange`, because they render their own dark-mode switch. The other viewers accept both props as optional.

## Minimal examples

```svelte
<script lang="ts">
  import { PdfViewer, DocxViewer, XlsxViewer, PptxViewer, CsvTsvViewer } from 'extend-ui-svelte';
  let isDark = $state(false);
  const setDark = (v: boolean) => (isDark = v);
</script>

<PdfViewer src="/files/invoice.pdf" fileName="invoice" defaultZoom="fit-width" {isDark} />
<DocxViewer src="/files/contract.docx" {isDark} onIsDarkChange={setDark} />
<XlsxViewer src="/files/rates.xlsx" {isDark} onIsDarkChange={setDark} />
<PptxViewer src="/files/deck.pptx" {isDark} />
<CsvTsvViewer data={'name,qty\nbolts,40\nnuts,12'} search {isDark} />
```

## Shared patterns

**Loading, error, and empty states are built in.** Every viewer renders a `role="status"` loading surface, a `role="alert"` error surface, and an empty prompt when it has no source. Do not wrap viewers in your own spinners. The only load callback is `PdfViewer`'s `onDocumentLoadSuccess(numPages)`. No viewer has an `onError` callback. To catch a bad URL before mounting, `fetch` it yourself first.

**Sizing.** `PdfViewer`, `XlsxViewer`, `PptxViewer`, and `CsvTsvViewer` take a numeric `height` in px, with defaults of 600, 480, 560, and 560. Virtualization depends on it, so set it explicitly when filling a panel. `DocxViewer` has no `height` prop. Its root is fixed at 640px tall by scoped CSS, toolbar included.

**Zoom.**
- `PdfViewer.defaultZoom` takes a scale (`1` means 100%) or `'fit-page' | 'fit-width' | 'automatic'`. The range is 0.1 to 2.
- `DocxViewer.defaultZoom` takes a **percentage** (`50` by default) or the same fit modes.
- `XlsxViewer`, `PptxViewer`, and `CsvTsvViewer` have no zoom.
- Zoom is uncontrolled: it resets to `defaultZoom` each time a new document loads.

**Page navigation.** `PdfViewer` and `DocxViewer` have Previous and Next buttons and a page indicator in the toolbar. `PdfViewer` reports the topmost visible page through `onActivePageChange`. No viewer exposes an imperative `goToPage` handle or a controlled page prop, so a parent cannot scroll a viewer to a page.

**Search.** Only `CsvTsvViewer` searches, and only with `search={true}`. Enter and Shift+Enter step through matches, the active cell is highlighted and scrolled into view, and Escape closes the search. The PDF, DOCX, XLSX, and PPTX viewers have no text search.

**Overlays and highlights.** Only `PdfViewer` has them, through its `pageOverlay` snippet. The snippet is laid out in unrotated page space at scale 1, so multiply coordinates by `scale`. The overlay layer has `pointer-events: none`, so set `pointer-events: auto` on any child that should be clickable. See `references/pdf-viewer.md`.

**Toolbar.**
- `showToolbar` exists on the PDF, DOCX, XLSX, and PPTX viewers.
- `showDownload`, `showUpload`, and a `toolbarActions` snippet exist on the PDF, DOCX, and PPTX viewers.
- An upload replaces the displayed document only until `src` changes.

**Dark mode.** The parent owns the theme. Each viewer adds a `dark` class and a `data-dark` attribute to its root. `onIsDarkChange` is called only by the DOCX and XLSX toolbar switches.

**SSR.** All engines load with a dynamic `import()` on the client, so viewers can be server-rendered. On the server they render the loading or empty state.

## Thumbnail sidebar

`DocumentViewerThumbnailSidebar` is a layout shell: a 10rem rail that sits inline at 768px and wider and slides over narrower viewers. You render the thumbnails. Pair it with `useElementWidth()` and `useInlineThumbnailSidebar(width)`, and show `DocumentViewerSidebarSkeleton` while thumbnails load. The parent container must be `position: relative; display: flex; overflow: hidden`. See `references/document-viewer-sidebar.md`.

Because no viewer exposes `goToPage`, a sidebar next to `PdfViewer` can show which page is active (from `onActivePageChange`), but clicking a thumbnail cannot scroll the viewer. `DocxViewer` already includes its own virtualized thumbnail list, opened with the toolbar's "Thumbnails" button, so it needs no external sidebar.

## Generic "open any file" viewer

Dispatch on the lowercased extension, falling back to the MIME type. Hold one object URL per `File` and revoke it on change. The full component is in `examples/UniversalDocumentViewer.svelte`. The core of it:

```ts
type Kind = 'pdf' | 'docx' | 'xlsx' | 'pptx' | 'csv' | 'tsv' | 'unsupported';
function kindOf(name: string, mime = ''): Kind {
  const ext = name.split('?')[0].split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'pdf' || mime === 'application/pdf') return 'pdf';
  if (ext === 'docx' || mime.includes('wordprocessingml')) return 'docx';
  if (['xlsx', 'xlsm', 'xls', 'ods'].includes(ext) || mime.includes('spreadsheetml')) return 'xlsx';
  if (ext === 'pptx' || mime.includes('presentationml')) return 'pptx';
  if (ext === 'tsv' || mime === 'text/tab-separated-values') return 'tsv';
  if (ext === 'csv' || mime === 'text/csv') return 'csv';
  return 'unsupported';
}
```

For TSV, pass `delimiter={'\t'}`. Auto-detection usually works, but an explicit delimiter is safer.

## References

- `references/pdf-viewer.md`: props, zoom helpers, overlay snippet, worker setup
- `references/docx-viewer.md`: props, zoom helpers, built-in thumbnails
- `references/xlsx-viewer.md`: props, grid keyboard behavior, `WorkbookSheetTabs`
- `references/pptx-viewer.md`: props, slide windowing, `PptxSlide`
- `references/csv-tsv-viewer.md`: props, `parseDelimitedText`, search
- `references/document-viewer-sidebar.md`: sidebar, skeleton, width helpers
- `examples/UniversalDocumentViewer.svelte`: file picker plus dispatch to the right viewer
- `examples/PdfReviewWithSidebar.svelte`: PDF with highlight overlays and a responsive page sidebar
