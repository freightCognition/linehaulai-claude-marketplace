# FileUpload

Source: `src/lib/components/file-upload/FileUpload.svelte`. A click-or-drop zone with an optional list of accepted files. It filters by type only. Uploading and size or count limits are up to you.

## Imports

```ts
import { FileUpload } from 'extend-ui-svelte';
import {
	FileUpload,
	DEFAULT_ACCEPT,
	DEFAULT_ACCEPTED_FILE_TYPES,
	formatBytes,
	matchesAccept,
	toUploadItems,
	type AcceptedFileType,
	type FileUploadItem
} from 'extend-ui-svelte/components/file-upload';
// registry copy-in: '$lib/components/file-upload/index.js' (needs file-thumbnail, engines, dark-mode)
```

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `accept` | `string` | `DEFAULT_ACCEPT` | Comma list of `.ext`, exact MIME, or `type/*`. Passed to the native input and enforced on drop. Empty string accepts everything. |
| `acceptedFileTypes` | `AcceptedFileType[]` | `DEFAULT_ACCEPTED_FILE_TYPES` (Image/IMG, PDF/PDF, Sheet/XLS) | Decorative icon cards above the title. Keyed by `label`, so labels must be unique. One entry gives a single centered card. |
| `browseLabel` | `string` | `'Browse files'` | Pill text when idle. |
| `draggingLabel` | `string` | `'Drop to add'` | Pill text while dragging over the zone. |
| `title` | `string` | `'Click to upload or drop files'` | Main line. |
| `description` | `string` | `'PDF, DOC/DOCX, XLSX, CSV, PNG, or JPG'` | Secondary line. Update it when you change `accept`. |
| `multiple` | `boolean` | `true` | When `false`, only the first accepted file is kept. Also set on the native input. |
| `showBorderBeam` | `boolean` | `true` | Animated conic-gradient border while dragging. Respects `prefers-reduced-motion`. |
| `showFileList` | `boolean` | `true` | Renders the accepted files below the zone with a `FileThumbnail`, name, type, size, and a "Ready" badge. |
| `class` / `className` | `string` | none | Both merged onto the root. |
| `isDark` | `boolean` | `false` | Dark palette. |
| `onIsDarkChange` | `(isDark: boolean) => void` | none | Accepted for parity. Never called. |
| `onFilesAccepted` | `(files: File[]) => void` | none | Raw accepted `File` objects. Use this to upload. |
| `onFilesChange` | `(files: FileUploadItem[]) => void` | none | Same files as `FileUploadItem`s with object URLs. Fires after `onFilesAccepted`. |

There are no snippets or slots.

## Exported helpers and types

```ts
interface FileUploadItem { id: string; name: string; type: string; size: number; url: string }
interface AcceptedFileType { label: string; glyph?: string }

const DEFAULT_ACCEPT: string; // .pdf,.doc,.docx,.xlsx,.csv,.png,.jpg,.jpeg + matching MIME types
const DEFAULT_ACCEPTED_FILE_TYPES: AcceptedFileType[];
function formatBytes(bytes: number): string;           // "0 B", "512 B", "1.5 KB", "2.0 MB", caps at GB
function matchesAccept(file: File, accept?: string): boolean;
function toUploadItems(files: FileList | File[]): FileUploadItem[]; // creates object URLs; you must revoke them
```

`FileUploadItem.id` is `${name}-${size}-${lastModified}`, so two identical files share an id. `type` falls back to `'Unknown type'`.

## Behavior

- Drop or pick, then filter with `matchesAccept`, then slice to one file if `!multiple`.
- If nothing passes, it shows a red "This file type is not supported here." and fires no callbacks. If some pass, the rest are dropped silently.
- Each commit replaces the whole internal list. It does not append. The old object URLs are revoked, and all URLs are revoked on destroy.
- The internal list cannot be read, cleared, or set from outside. Remount the component (for example `{#key resetCount}`) to clear it.
- The native input is reset after each pick, so choosing the same file again fires again.

## Keyboard and accessibility

- The drop zone is `role="button"` with `tabindex="0"`. Enter or Space opens the file dialog, and so does a click.
- The hidden input has `tabindex="-1"` and no `name`.
- The icon cluster is `aria-hidden`. The rejection message is plain text, not a live region. Add your own `aria-live` status if you report limit errors.

## Full example: validated upload with progress list

```svelte
<script lang="ts">
	import { FileUpload } from 'extend-ui-svelte';
	import { formatBytes } from 'extend-ui-svelte/components/file-upload';

	type Row = { file: File; state: 'queued' | 'uploading' | 'done' | 'error'; message?: string };

	const MAX_BYTES = 20 * 1024 * 1024;
	let rows = $state<Row[]>([]);
	let resetKey = $state(0);

	function onFilesAccepted(files: File[]) {
		const next: Row[] = files.map((file) =>
			file.size > MAX_BYTES
				? { file, state: 'error', message: `Larger than ${formatBytes(MAX_BYTES)}` }
				: { file, state: 'queued' }
		);
		rows = [...rows, ...next]; // FileUpload replaces its list per drop; we append
		for (const row of next) if (row.state === 'queued') void upload(row);
	}

	async function upload(row: Row) {
		const index = rows.indexOf(row);
		rows[index].state = 'uploading';
		try {
			const body = new FormData();
			body.append('file', row.file);
			const res = await fetch('/api/files', { method: 'POST', body });
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			rows[index].state = 'done';
		} catch (error) {
			rows[index].state = 'error';
			rows[index].message = (error as Error).message;
		}
	}
</script>

{#key resetKey}
	<FileUpload
		accept=".pdf,image/png,image/jpeg"
		description="PDF, PNG or JPG up to 20 MB"
		acceptedFileTypes={[{ label: 'PDF', glyph: 'PDF' }, { label: 'Image', glyph: 'IMG' }]}
		showFileList={false}
		{onFilesAccepted}
	/>
{/key}

<ul aria-live="polite">
	{#each rows as row, i (i)}
		<li>{row.file.name} ({formatBytes(row.file.size)}): {row.state} {row.message ?? ''}</li>
	{/each}
</ul>
<button onclick={() => { rows = []; resetKey++; }}>Clear</button>
```

## Gotchas

- There are no `maxSize`, `maxFiles`, `disabled`, `name`, or `value` props. Do not invent them.
- The `url` values from `onFilesChange` are revoked by the component on the next drop. Create your own with `URL.createObjectURL(file)` if they need to outlive it.
- The built-in list says "Ready" for every accepted file even if your code rejects it. Use `showFileList={false}` with your own list when you validate.
- The drop handler checks the file name extension or the `file.type` reported by the browser. Validate the content again on the server.
- In SvelteKit SSR the component renders fine. Object URLs are only created after user interaction.
