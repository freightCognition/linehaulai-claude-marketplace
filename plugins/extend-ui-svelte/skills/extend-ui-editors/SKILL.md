---
name: extend-ui-editors
description: This skill should be used when the user asks to edit a PDF, rotate/reorder/delete PDF pages, build a Word or .docx editor, build a spreadsheet or .xlsx editor, edit cells or formulas in the browser, capture a signature, add e-signature, sign a PDF, stamp a signature onto a PDF, or save/export/upload an edited document in a Svelte 5 app using extend-ui-svelte (PdfEditor, DocxEditor, XlsxEditor, ESignature).
---

# extend-ui-svelte editors

Four editing components from `extend-ui-svelte`, a Svelte 5 port of extend-hq/ui. For install, SSR rules, the PDF/DOCX/XLSX engines, and the parent-controlled dark-mode contract, read the core skill first: [`../extend-ui-svelte/SKILL.md`](../extend-ui-svelte/SKILL.md). This skill covers what happens after the document is on screen: editing it, reading the changes back, and saving the result.

## Pick the component

| Need | Component | What it can actually edit |
|---|---|---|
| Rotate, reorder, delete PDF pages | `PdfEditor` (alias `PDFEditor`) | Page-level edits only. No annotations, forms, redaction, text edits, or signing. |
| Light rich-text edit of a .docx | `DocxEditor` (alias `DocxEditorPreview`) | Paragraphs, H1–H3, bold, italic, bulleted and numbered lists. Export is **lossy**. |
| Edit cells and formulas in a workbook | `XlsxEditor` (alias `XlsxEditorPreview`) | Values, formulas, bold/align/fill (fill and style are not written on export), all sheets. |
| Draw a signature and stamp it on a PDF | `ESignature` (alias `ESignatureBlock`) | One drawn signature on one page, placed by numeric coordinates. |

If the user needs something outside the "actually edit" column (PDF annotations, tracked changes, number formats, multiple signers), say so up front. Those are known gaps against upstream React, not missing configuration. See "Parity gaps" below.

## Imports

```ts
// Components: package root
import { PdfEditor, DocxEditor, XlsxEditor, ESignature } from 'extend-ui-svelte';

// Helpers and types: per-component subpath (package.json "./components/*")
import { exportEditedPdf, type EditedPdfPage } from 'extend-ui-svelte/components/pdf-editor';
import { exportDocxBytes, DOCX_MIME_TYPE } from 'extend-ui-svelte/components/docx-editor';
import { sheetsToXlsxBytes, type XlsxCellChange } from 'extend-ui-svelte/components/xlsx-editor';
import { embedSignaturePng, resolvePlacement } from 'extend-ui-svelte/components/e-signature';
```

The root barrel exports only the components and `PdfEditorProps`/`PDFEditorProps`/`ESignatureProps`. Every helper comes from the subpath. With the shadcn-svelte registry copy-in, import the same names from the copied folder, e.g. `$lib/components/pdf-editor/index.js`.

## Minimal examples

```svelte
<script lang="ts">
	import { PdfEditor, DocxEditor, XlsxEditor, ESignature } from 'extend-ui-svelte';
	let isDark = $state(false);
</script>

<PdfEditor src="/files/contract.pdf" {isDark} onSave={({ buffer, fileName }) => console.log(fileName, buffer.byteLength)} />

<!-- isDark and onIsDarkChange are REQUIRED props on DocxEditor and XlsxEditor -->
<DocxEditor src="/files/memo.docx" {isDark} onIsDarkChange={(v) => (isDark = v)} onExport={(bytes) => console.log(bytes.byteLength)} />

<XlsxEditor src="/files/budget.xlsx" {isDark} onIsDarkChange={(v) => (isDark = v)} onCellChange={(c) => console.log(c)} />

<ESignature file="/files/nda.pdf" fileName="nda" {isDark} onSignedDownload={(name) => console.log(name)} />
```

## Edit lifecycle

None of these components exposes a bindable document value or an imperative handle. Changes come out through callbacks, and export runs from the component's own toolbar button. Plan the save path around that.

**PdfEditor**
1. Load: `src` is a URL, `ArrayBuffer`, `Uint8Array`, `Blob`, or `File`. `onDocumentLoadSuccess({ numPages, documentId, fileName })` or `onDocumentLoadError(message)`.
2. Edit: each rotate, move, delete, or reset calls `onPagesChange(pages)` with the full `EditedPdfPage[]` (`{ sourcePage, rotation }`, in the new order, deleted pages left out).
3. Save: the Download button or Cmd/Ctrl+S builds the PDF with pdf-lib, **triggers a browser download**, then calls `onSave({ buffer: ArrayBuffer, fileName })`.
4. Save without a download: set `showDownload={false}`, keep the latest `pages` from `onPagesChange`, and call `exportEditedPdf(sourceBytes, { pages })` yourself (it returns a `Uint8Array`). Setting `showDownload={false}` also turns off Cmd/Ctrl+S.

**DocxEditor**
1. Load: `src` is typed `string` (a URL). For a local `File`, pass `URL.createObjectURL(file)`, or let the user pick one with the built-in Upload button.
2. Edit: a `contenteditable` surface. **There is no change callback.** The editor's HTML is internal state.
3. Save: the "Export .docx" button calls `onExport(bytes: Uint8Array)` and then downloads `<fileName>.docx`. Both always happen.
4. Export rebuilds a minimal package from the editor blocks, so tables, images, styles, headers, and footers in the source are dropped. Warn users before they overwrite an original.

**XlsxEditor**
1. Load: `data` (`ArrayBuffer | Uint8Array`) takes precedence over `src` (URL, fetched on the client). Changing either one resets every edit.
2. Edit: each committed cell edit calls `onCellChange({ sheet, row, col, value })`. Row and column are zero-based. For a formula, `value` is the text including `=`, for example `"=SUM(A1:A3)"`.
3. Save: the "Export .xlsx" button writes every sheet with SheetJS, **downloads the file**, then calls `onExport(bytes, fileName)`. Bold, alignment, and fill are dropped on export.

**ESignature**
1. Load: `file` (or the alias `src`) is a URL string, fetched on the client. Use `URL.createObjectURL(file)` for local files.
2. Draw: `onSignatureChange(hasSignature)` fires after each stroke and after Clear.
3. Place: "Place signature" stamps a PNG onto the original bytes. Placing again replaces the earlier stamp instead of adding a second one. `positionX`, `positionY`, `signatureWidth`, `signatureHeight`, and `scale` are `$bindable`.
4. Save: "Download signed PDF" downloads `<name>-signed.pdf` and calls `onSignedDownload(fileName)`. **No callback returns the signed bytes.** To upload a signed PDF, build the flow with the helpers instead (next section).

## Saving edited output

Every export path ends in a `Uint8Array` or `ArrayBuffer`. Wrap it in a Blob with the right MIME type:

```ts
const MIME = {
	pdf: 'application/pdf',
	docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX_MIME_TYPE
	xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
};

async function upload(bytes: Uint8Array | ArrayBuffer, name: string, type: string) {
	const body = new FormData();
	body.append('file', new Blob([bytes as BlobPart], { type }), name);
	const res = await fetch('/api/documents', { method: 'POST', body });
	if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
}
```

- Use PdfEditor's `onSave` (download already happened) or `exportEditedPdf` (no download).
- Use DocxEditor's `onExport` (the download still fires).
- Use XlsxEditor's `onExport` (the download still fires). For a download-free save, the component offers nothing. Rebuild sheets yourself and call `sheetsToXlsxBytes(sheets)` (see `references/xlsx-editor.md`).
- For a server download, use a SvelteKit `+server.ts` that returns the stored bytes with `Content-Type` and `Content-Disposition: attachment`.

## E-signature: capture and stamp

There are two routes:

1. **Drop-in.** `<ESignature file={url} />` handles drawing, placing, previewing, and downloading. Choose it when a download is the end of the flow.
2. **Custom flow with upload.** Use `signature_pad` directly for capture and the helpers for stamping:

```ts
import SignaturePad from 'signature_pad';
import { dataUrlToBytes, defaultPlacementForPage, embedSignaturePng, resolvePlacement }
	from 'extend-ui-svelte/components/e-signature';

const png = dataUrlToBytes(pad.toDataURL('image/png'));          // pad: SignaturePad
const box = defaultPlacementForPage(612, 792);                    // or your own x/y/width/height
const placement = resolvePlacement({ ...box, page: 1, scale: 1, pageCount });
const signed = await embedSignaturePng(pdfBytes, png, placement); // Uint8Array
```

Coordinates are **PDF points from the bottom-left corner** (pdf-lib convention), not CSS pixels from the top-left. A Letter page is 612×792 pt. Load `signature_pad` inside `onMount` with `await import('signature_pad')`, because it needs a canvas. `pdf-lib` and the `sign-pdf` helpers are safe during SSR. With pnpm or another strict installer, add `signature_pad` and `pdf-lib` as direct dependencies before importing them in app code. Full flow: `examples/sign-and-upload-pdf.svelte`.

## Dark mode

All four take `isDark` and never flip it themselves (enforced by the parity suite). The core skill covers the contract. Per editor:
- `DocxEditor` and `XlsxEditor` **require** `isDark` and `onIsDarkChange` in their TS props. Their toolbars show a dark-mode switch that calls `onIsDarkChange(!isDark)`.
- `PdfEditor` and `ESignature` render no switch. `onIsDarkChange` is accepted and never called.

## SSR and lifecycle gotchas

- Every editor loads its engine in `onMount` or `$effect`, so server renders show only the empty or loading shell. No `{#if browser}` guard is needed.
- **Unmounting loses edits.** No editor persists state. Save, or capture `onPagesChange`/`onCellChange`, before navigating away. Add a `beforeNavigate` or `beforeunload` guard if edits matter.
- **There is no undo or redo** in any editor. PdfEditor's Reset is the only revert.
- A new `src` or `data` reference resets the editor. Do not create a fresh `Uint8Array` on every render (for example, inside `$derived` from a changing object).
- Large files: PdfEditor and XlsxEditor virtualize their lists and rows. XlsxEditor parses **every sheet up front**, and upstream's read-only mode above 5 MB is not ported. DocxEditor puts the whole document on one contenteditable surface with no page virtualization.
- `class` and `className` are both accepted and merged on every component.

## Parity gaps vs upstream React (from `src/lib/parity/port-parity.test.ts`)

- **PdfEditor** does not accept: `defaultMode`, `annotationAuthor`, `colorPresets`, `features`, `toolbarActions`, `selectionActions`, `persistSignatures`, `stampManifests`, `signatureFontsStylesheetUrl`, `resolveScrollAreaViewport`, `renderPageOverlay`, `onModeChange`, `onAnnotationEvent`, `onAnnotationsChange`, `onFormValuesChange`, `onRedactionsApplied`, `onCapture`, `onToast`, `onSelectionAction`. It has no imperative handle and no multi-page selection.
- **DocxEditor and XlsxEditor** match the full upstream prop list and add port-only props (`showToolbar`, `readOnly`, `onExport` for DOCX; `data`, `rowHeight`, `height`, `overscan`, `onCellChange`, `onExport` for XLSX). Features are narrower: see the references.
- **ESignature** accepts upstream's only prop, `file`. Fields, recipients, the draggable placement overlay, and signing states are not ported.

## References and examples

- `references/pdf-editor.md`, `references/docx-editor.md`, `references/xlsx-editor.md`, `references/e-signature.md` cover each component's full props table, callbacks, exported helpers and types, keyboard behavior, a realistic example, and gotchas.
- `examples/sign-and-upload-pdf.svelte`: custom signature capture, stamping with pdf-lib, then download and upload.
- `examples/edit-spreadsheet-save-to-api.svelte`: XlsxEditor with change tracking and `onExport` saving to an API.
