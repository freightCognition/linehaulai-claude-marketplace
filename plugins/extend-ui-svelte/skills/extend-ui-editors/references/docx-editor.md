# DocxEditor reference

Source: `src/lib/components/docx-editor/DocxEditor.svelte`, `export.ts`, `index.ts`.

```ts
import { DocxEditor, DocxEditorPreview } from 'extend-ui-svelte';
import {
	type DocxEditorProps, type DocxEditorBlock, type DocxEditorBlockType, type DocxEditorRun,
	blocksToEditorHtml, elementToBlocks, blocksToDocumentXml, buildDocxParts, exportDocxBytes,
	escapeXml, ensureDocxExtension, formatDocumentName, normalizeZoomScale,
	DEFAULT_ZOOM_SCALE, DOCX_MIME_TYPE, DOCX_UPLOAD_ACCEPT, ZOOM_OPTIONS
} from 'extend-ui-svelte/components/docx-editor';
// Registry copy-in: same names from '$lib/components/docx-editor/index.js'
```

`DocxEditorProps` is not exported from the package root. Import it from the subpath.

How it works: docx-preview renders the source offscreen. Its paragraphs are extracted into a native `contenteditable` surface and formatted with `document.execCommand`. Export rebuilds a minimal .docx package from the edited blocks with jszip.

## Props

No props are `$bindable`.

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `isDark` | `boolean` | `false` | **yes (TS)** | Parent-controlled theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | **yes (TS)** | Called by the toolbar's "Toggle dark mode" switch. |
| `src` | `string` | — | | DOCX URL. For a `File`, pass `URL.createObjectURL(file)`. |
| `fileName` | `string` | derived | | Toolbar and export name. Fallbacks: the uploaded file's name, the last URL path segment, then `document.docx`. |
| `defaultZoomScale` | `number` | `100` | | Must be one of `ZOOM_OPTIONS` (`50, 75, 90, 100, 110, 125, 150, 175, 200`); other values fall back to 100. Reset whenever `src` changes. |
| `showToolbar` | `boolean` | `true` | | Formatting toolbar. (Port-only.) |
| `readOnly` | `boolean` | `false` | | Turns off editing and formatting. Upload and Export still work. (Port-only.) |
| `onExport` | `(bytes: Uint8Array) => void` | — | | Called with the .docx bytes before the download. (Port-only.) |
| `class` / `className` | `string` | `''` | | Merged together. |

## Callbacks and change tracking

- There is **no `onChange` or input callback.** Edits stay inside the contenteditable surface and come out only through Export (`onExport`).
- An upload through the toolbar replaces `src` until `src` changes. No callback reports it.

## Exported helpers

```ts
type DocxEditorBlockType = 'paragraph' | 'heading1' | 'heading2' | 'heading3' | 'bullet' | 'number';
interface DocxEditorRun { text: string; bold?: boolean; italic?: boolean }
interface DocxEditorBlock { type: DocxEditorBlockType; runs: DocxEditorRun[] }

exportDocxBytes(blocks): Promise<Uint8Array>   // jszip, lazy import; build a .docx without the component
elementToBlocks(root: HTMLElement): DocxEditorBlock[]  // leaf h1-h6/p/li/div into blocks
blocksToEditorHtml(blocks): string
blocksToDocumentXml(blocks): string            // word/document.xml
buildDocxParts(documentXml): Record<string, string>
ensureDocxExtension(name), formatDocumentName(fileName, url), normalizeZoomScale(n), escapeXml(text)
```

`exportDocxBytes` also works without the component. Use it to generate a simple .docx from structured data:

```ts
const bytes = await exportDocxBytes([
	{ type: 'heading1', runs: [{ text: 'Load confirmation' }] },
	{ type: 'paragraph', runs: [{ text: 'Rate: ', bold: true }, { text: '$2,400' }] },
	{ type: 'bullet', runs: [{ text: 'Pickup 08:00' }] }
]);
```

## Keyboard

The toolbar has no custom shortcuts. The surface is a browser `contenteditable` with `role="textbox"`, so native editing keys apply, and browsers usually map Cmd/Ctrl+B and Cmd/Ctrl+I to bold and italic. The toolbar has Bold, Italic, Block style (Paragraph, H1, H2, H3), Bulleted list, Numbered list, zoom −/+/select, Upload, "Export .docx", and "Toggle dark mode". Undo is only the browser's native contenteditable undo. The component has no undo/redo buttons.

## Snippets

None.

## Example: edit a user-uploaded file and save to an API

```svelte
<script lang="ts">
	import { DocxEditor } from 'extend-ui-svelte';
	import { DOCX_MIME_TYPE } from 'extend-ui-svelte/components/docx-editor';

	let { file }: { file: File } = $props();
	let isDark = $state(false);
	let status = $state('');

	// One object URL per file, revoked when the file changes or the component unmounts.
	let url = $state<string>();
	$effect(() => {
		const next = URL.createObjectURL(file);
		url = next;
		return () => URL.revokeObjectURL(next);
	});

	async function onExport(bytes: Uint8Array) {
		status = 'Uploading…';
		const body = new FormData();
		body.append('file', new Blob([bytes as BlobPart], { type: DOCX_MIME_TYPE }), file.name);
		const res = await fetch('/api/documents', { method: 'POST', body });
		status = res.ok ? 'Saved' : `Upload failed (${res.status})`;
	}
</script>

<p>Export keeps text, headings, bold, italic, and lists only. Tables, images, and styles are dropped.</p>
<DocxEditor src={url} fileName={file.name} {isDark} onIsDarkChange={(v) => (isDark = v)} {onExport} />
<p>{status}</p>
```

## Gotchas

- **Lossy round-trip.** Source tables, images, styles, fonts, colors, headers, footers, comments, and tracked changes are dropped. Never silently overwrite the original file with the export.
- Export always triggers a browser download as well as `onExport`. It cannot be suppressed.
- Uploads accept `.docx` only (`DOCX_UPLOAD_ACCEPT`). Legacy `.doc` is rejected.
- The document is one surface with no page breaks, page count, or virtualization, so very long documents get slow.
- Unmounting discards edits, and the component offers no autosave. Export before navigating away.
- `document.execCommand` is deprecated but still works in current browsers. Formatting depends on it.
- Not ported (deliberate, from the component header): undo/redo buttons, fonts, color, highlight, links, alignment, borders, comments, tracked changes, tables, images, and page thumbnails. The prop list matches upstream exactly; the parity ledger records no missing props.
