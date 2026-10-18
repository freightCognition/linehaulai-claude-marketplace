# PdfEditor reference

Source: `src/lib/components/pdf-editor/PdfEditor.svelte`, `page-model.ts`, `index.ts`.

```ts
import { PdfEditor, PDFEditor, type PdfEditorProps } from 'extend-ui-svelte';
import {
	createEditState, deleteEditPage, exportEditedPdf, getPdfFileName, moveEditPage,
	resetEditState, rotateEditPage,
	type EditedPdfPage, type PdfEditState, type PdfRotateDirection,
	type PdfEditorDocumentInfo, type PdfEditorSaveResult, type PdfEditorZoomLevel
} from 'extend-ui-svelte/components/pdf-editor';
// Registry copy-in: same names from '$lib/components/pdf-editor/index.js'
```

Scope: page-level edits only (rotate, reorder, delete, reset, download). Rendering uses the shared PDF.js engine. Export uses pdf-lib. Both load on the client.

## Props

No props are `$bindable`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `src` | `string \| ArrayBuffer \| Uint8Array \| Blob` (a `File` is a `Blob`) | — | PDF URL or bytes. Empty shows the upload prompt. |
| `fileName` | `string` | derived | Download name (`.pdf` added if missing). Fallbacks: the last URL path segment (not for `blob:` or `data:` URLs), then the `File` name, then `document.pdf`. |
| `defaultZoom` | `number \| 'fit-page' \| 'fit-width' \| 'automatic'` | `'fit-width'` | Initial zoom. Re-applied each time a new document loads. Uncontrolled after that. |
| `showToolbar` | `boolean` | `true` | Shows the top toolbar (zoom, Download, Reset, Upload). |
| `showDownload` | `boolean` | `true` | Shows the Download button. `false` also disables Cmd/Ctrl+S. |
| `showUpload` | `boolean` | `true` | Shows the Upload control. |
| `onDocumentLoadSuccess` | `(info: PdfEditorDocumentInfo) => void` | — | `{ numPages, documentId, fileName }`. |
| `onDocumentLoadError` | `(message: string) => void` | — | Document load failures only. An engine load failure shows an error state without calling this. |
| `onActivePageChange` | `(pageNumber: number) => void` | — | 1-based position of the selected page in the edited order. |
| `onPagesChange` | `(pages: EditedPdfPage[]) => void` | — | Called after every rotate, move, delete, or reset. (Port-only.) |
| `onSave` | `(result: PdfEditorSaveResult) => void` | — | `{ buffer: ArrayBuffer, fileName }`. Fires **after** the browser download. |
| `onPdfUpload` | `(file: File) => void` | — | A file was chosen with Upload. The upload replaces `src` until `src` changes. |
| `isDark` | `boolean` | `false` | Parent-controlled theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Typed but never called (the editor has no dark-mode switch). |
| `height` | `number` | `600` | Body height in px. (Port-only.) |
| `pageWidth` / `pageHeight` | `number` | `612` / `792` | Fallback page size in px at zoom 1, used until the engine reports real sizes. (Port-only.) |
| `class` / `className` | `string` | `''` | Merged together. |

## Types and helpers

```ts
interface EditedPdfPage { sourcePage: number /* 1-based in original */; rotation: number /* 0|90|180|270 cw */ }
interface PdfEditState { pages: EditedPdfPage[] }
type PdfRotateDirection = 'clockwise' | 'counter-clockwise';

createEditState(pageCount): PdfEditState            // every page, in order, unrotated
resetEditState(pageCount): PdfEditState             // same as createEditState
rotateEditPage(state, index, direction): PdfEditState
deleteEditPage(state, index): PdfEditState          // never removes the last page
moveEditPage(state, fromIndex, toIndex): PdfEditState
exportEditedPdf(sourceBytes: Uint8Array, state): Promise<Uint8Array>  // pdf-lib, lazy import
getPdfFileName(fileName?, src?): string
```

The helpers are pure and return a new state; an out-of-range index returns the input unchanged. `exportEditedPdf` adds each page's rotation on top of any rotation the source page already has, and loads pdf-lib with `ignoreEncryption: true`.

## Keyboard

- Cmd/Ctrl+S downloads (only when `showDownload`). Cmd/Ctrl+`=`/`+` zooms in, Cmd/Ctrl+`-` zooms out, Cmd/Ctrl+`0` fits the page. Shortcuts work only while the editor has focus and are ignored inside inputs.
- In the page list (a listbox), ArrowUp, ArrowDown, Home, and End move the selection.
- In the delete confirmation dialog, focus is trapped, Escape closes it, and Tab cycles between the buttons.
- Not ported: undo/redo, print, search, Delete key for pages.

## Snippets

None. The editor takes no `children` or snippet props.

## Example: edit, then upload without a download

```svelte
<script lang="ts">
	import { PdfEditor } from 'extend-ui-svelte';
	import { exportEditedPdf, type EditedPdfPage } from 'extend-ui-svelte/components/pdf-editor';

	let { file }: { file: File } = $props();
	let isDark = $state(false);
	let pages = $state<EditedPdfPage[] | null>(null);
	let saving = $state(false);
	let message = $state('');

	async function save() {
		if (!pages) return;
		saving = true;
		try {
			const source = new Uint8Array(await file.arrayBuffer());
			const edited = await exportEditedPdf(source, { pages });
			const body = new FormData();
			body.append('file', new Blob([edited as BlobPart], { type: 'application/pdf' }), file.name);
			const res = await fetch('/api/documents', { method: 'POST', body });
			message = res.ok ? 'Saved' : `Save failed (${res.status})`;
		} finally {
			saving = false;
		}
	}
</script>

<PdfEditor
	src={file}
	{isDark}
	showDownload={false}
	height={700}
	onDocumentLoadSuccess={({ numPages }) => (pages = Array.from({ length: numPages }, (_, i) => ({ sourcePage: i + 1, rotation: 0 })))}
	onPagesChange={(next) => (pages = next)}
/>
<button onclick={save} disabled={!pages || saving}>{saving ? 'Saving…' : 'Save to server'}</button>
<p>{message}</p>
```

Seed `pages` in `onDocumentLoadSuccess`, because `onPagesChange` only fires after the first edit.

## Gotchas

- `onSave` cannot cancel or replace the download. For server-only saves, use `showDownload={false}` and `exportEditedPdf`.
- When `src` is a URL, Download re-fetches it to get the bytes, so the URL must stay reachable and CORS-readable.
- Every new document load resets the edits. Passing a new `src` reference discards unsaved work.
- Delete asks for confirmation and refuses to remove the last page, showing "A document needs at least one page."
- Not ported (parity ledger): annotations, signing, forms, redaction, search, print, password prompts, insert/append/extract pages, multi-select, the imperative handle, and the props listed in SKILL.md. For signatures, use ESignature or the `sign-pdf` helpers.
