---
name: extend-ui-files-primitives
description: This skill should be used when the user asks to add file upload, a drop zone, or drag and drop files, show file thumbnails or a PDF page preview, build a file browser or file tree, open a file picked from a tree, use the color picker, toggle, toggle group, group or button group component, or wire these into a form in an app built with the extend-ui-svelte Svelte 5 library (FileUpload, FileThumbnail, FileSystem, ColorPicker, ColorPickerPanel, Toggle, ToggleGroup, Group).
---

# extend-ui-svelte: files and primitives

Use this skill for six components of `extend-ui-svelte` (a Svelte 5 port of extend-hq/ui): `FileUpload`, `FileThumbnail`, `FileSystem`, `Group`, `ColorPicker`, and `Toggle`. For install, SSR, dark mode, and the PDF engine, read the core skill at `../extend-ui-svelte/SKILL.md` first. For opening a file in a viewer, use `../extend-ui-viewers/SKILL.md`.

Full prop tables live in `references/`. Read the matching file before you write non-trivial code:

| Component | Reference |
| --- | --- |
| FileUpload | `references/file-upload.md` |
| FileThumbnail | `references/file-thumbnail.md` |
| FileSystem | `references/file-system.md` |
| Group, GroupText, GroupSeparator | `references/group.md` |
| ColorPicker, ColorPickerPanel | `references/color-picker.md` |
| Toggle, ToggleGroup, ToggleGroupItem | `references/toggle.md` |

Complete working pages are in `examples/`: `upload-thumbnails-viewer.svelte` (upload, thumbnail grid, open in the PDF viewer) and `file-browser-viewer.svelte` (tree plus viewer pane plus toolbar primitives).

## Imports

The package entry exports only the component classes for the file components. Helpers and types come from the per-component subpath, which `package.json` exposes as `./components/*`.

```ts
import { FileUpload, FileThumbnail, FileSystem } from 'extend-ui-svelte';
import { Group, GroupText, GroupSeparator, ColorPicker, ColorPickerPanel, Toggle, ToggleGroup, ToggleGroupItem } from 'extend-ui-svelte';

// Helpers and types: use the subpath
import { formatBytes, matchesAccept, toUploadItems, type FileUploadItem } from 'extend-ui-svelte/components/file-upload';
import type { FileSystemItem, FileSystemFileItem } from 'extend-ui-svelte/components/file-system';
import type { ToggleChangeEventDetails } from 'extend-ui-svelte/components/toggle';
```

With the registry copy-in install, the same modules live at `$lib/components/<name>/index.js` (for example `import { FileUpload } from '$lib/components/file-upload/index.js'`). The copied files import `../../dark-mode.js`, `../../utils.js`, and `../../engines/pdf/index.js`, so `dark-mode`, `utils`, and `engines` must sit at `$lib/` too. `file-upload` depends on `file-thumbnail`, and `toggle` depends on `group`.

## Styling: two families

- `FileUpload`, `FileThumbnail`, and `FileSystem` ship scoped CSS. They work without Tailwind. Size a `FileThumbnail` with a wrapper element or a global/Tailwind class, because a parent's scoped `<style>` does not reach a child component's root.
- `Group`, `Toggle`, `ToggleGroup`, and `ColorPicker` render Tailwind utility classes that expect shadcn-style tokens (`bg-muted`, `border-input`, `ring-ring`, `bg-popover`, `bg-accent`). The consuming app must run Tailwind v4 with those tokens and scan the library's files. `cn` here has no tailwind-merge, so a conflicting class you pass is appended, not swapped.

## When to use each

- **FileUpload**: a click-or-drop zone that filters by `accept`, then hands you `File[]`. It does not upload, and it has no size or count limit.
- **FileThumbnail**: a square (or page-shaped) preview tile from an image URL, a snippet, or a PDF page it renders itself.
- **FileSystem**: a keyboard-navigable tree built from a flat list of paths (S3/R2 style manifests). It emits selection and open events. It does not show the file.
- **Group**: join buttons, inputs, and text into one segmented control. Also exported as `ButtonGroup`.
- **ColorPicker**: an OKLCH plane plus hue and opacity sliders, with hex, rgb, hsl, and oklch text entry. `onChange` always gets a hex string.
- **Toggle / ToggleGroup**: a pressed or unpressed button, or a single or multi-select set of them.

## Minimal examples

```svelte
<script lang="ts">
	import { FileUpload, FileThumbnail, FileSystem, Group, GroupSeparator, ColorPicker, Toggle, ToggleGroup, ToggleGroupItem } from 'extend-ui-svelte';
	import type { FileSystemItem } from 'extend-ui-svelte/components/file-system';

	let files = $state<File[]>([]);
	let selectedPath = $state<string | null>(null);
	let color = $state('#2563eb');
	let bold = $state(false);
	let align = $state<string[]>(['left']);
	const items: FileSystemItem[] = [{ kind: 'file', path: 'invoices/2026/jan.pdf', contentType: 'application/pdf' }];
</script>

<FileUpload accept=".pdf,image/*" onFilesAccepted={(f) => (files = f)} />

<div class="size-24">
	<FileThumbnail file={{ name: 'jan.pdf', type: 'application/pdf' }} pdfUrl="/jan.pdf" width={192} />
</div>

<FileSystem {items} bind:selectedPath onFileOpen={(file, url) => console.log(file.path, url)} />

<Group>
	<button data-slot="button">Prev</button>
	<GroupSeparator />
	<button data-slot="button">Next</button>
</Group>

<ColorPicker value={color} onChange={(hex) => (color = hex)} label="Brand color" />

<Toggle pressed={bold} onPressedChange={(next) => (bold = next)} aria-label="Bold">B</Toggle>

<ToggleGroup value={align} onValueChange={(v) => (align = v)}>
	<ToggleGroupItem value="left">Left</ToggleGroupItem>
	<ToggleGroupItem value="center">Center</ToggleGroupItem>
</ToggleGroup>
```

## Flow: drag-and-drop upload with validation, then send to a server

1. Set `accept` to a comma list of extensions, exact MIME types, or `type/*`. `FileUpload` drops files that do not match. If none match it shows "This file type is not supported here." and does not call your callbacks.
2. Set `multiple={false}` to keep only the first accepted file.
3. Enforce size and count limits yourself in `onFilesAccepted`, because the component has no props for them. Use `formatBytes` for messages.
4. Upload the `File` objects with `fetch` and `FormData`. Track progress and errors in your own state.
5. To show your own status rows (rejected, uploading, done), set `showFileList={false}`. The built-in list marks every accepted file "Ready", including ones your limits rejected.

```svelte
<script lang="ts">
	import { FileUpload } from 'extend-ui-svelte';
	import { formatBytes } from 'extend-ui-svelte/components/file-upload';

	const MAX_BYTES = 10 * 1024 * 1024;
	const MAX_FILES = 5;
	let errors = $state<string[]>([]);
	let status = $state<Record<string, 'uploading' | 'done' | 'failed'>>({});

	async function handle(files: File[]) {
		errors = files
			.filter((f) => f.size > MAX_BYTES)
			.map((f) => `${f.name} is over ${formatBytes(MAX_BYTES)}`);
		const ok = files.filter((f) => f.size <= MAX_BYTES);
		if (ok.length > MAX_FILES) errors.push(`Only the first ${MAX_FILES} files were kept`);
		for (const file of ok.slice(0, MAX_FILES)) {
			status[file.name] = 'uploading';
			const body = new FormData();
			body.append('file', file);
			const res = await fetch('/api/upload', { method: 'POST', body });
			status[file.name] = res.ok ? 'done' : 'failed';
		}
	}
</script>

<FileUpload accept=".pdf,.png,.jpg" showFileList={false} onFilesAccepted={handle} />
```

Each drop replaces the previous list. It does not append. Keep your own array if users add files in several drops.

## Flow: thumbnails for uploaded files

- Images: pass `previewImageUrl={URL.createObjectURL(file)}`.
- PDFs: pass `pdfFile={file}`, or `pdfUrl`, plus `pageNumber` and `width`. Only that page renders, on the client.
- Anything else: pass neither and you get the neutral fallback tile, or pass a `previewContent` snippet.
- The `file` prop is required by the type but not used to build the preview. Always pass a preview source.
- Create your own object URLs from the `File` objects. Revoke them when you remove the file. Do not keep the `url` values from `onFilesChange`, because `FileUpload` revokes them on the next drop and on destroy.

See `examples/upload-thumbnails-viewer.svelte`.

## Flow: file browser and opening a file in a viewer

1. Build a flat `FileSystemItem[]`. Folders are optional, because missing parent folders are inferred from the file paths.
2. Use `bind:selectedPath` for selection, or `onSelectionChange` for the full item.
3. Handle `onFileOpen(file, url)`. It fires on double-click or Enter. The `url` is `file.url`, or else the result of `getFileUrl(file)` (sync or async, for example a presigned URL), or `null` if that throws. Without `onFileOpen` nothing happens.
4. Route on `file.contentType` or the extension, and render `PdfViewer`, `DocxViewer`, `XlsxViewer`, or `CsvViewer` with `src={url}`. Read `../extend-ui-viewers/SKILL.md` for viewer props. The viewers need client-only rendering, as the core skill explains.

See `examples/file-browser-viewer.svelte`.

## Flow: primitives in forms

Only `FileSystem.selectedPath` is `$bindable`. `ColorPicker`, `Toggle`, and `ToggleGroup` are controlled-by-callback, so `bind:value` and `bind:pressed` do not write back. Mirror state with `$state` and the callback, then put it in a hidden input for native form posts:

```svelte
<script lang="ts">
	import { ColorPicker, Toggle, ToggleGroup, ToggleGroupItem } from 'extend-ui-svelte';
	let color = $state('#111827');
	let notify = $state(true);
	let tags = $state<string[]>([]);
</script>

<form method="POST">
	<ColorPicker value={color} onChange={(c) => (color = c)} label="Accent" />
	<input type="hidden" name="accent" value={color} />

	<Toggle pressed={notify} onPressedChange={(p) => (notify = p)} variant="outline">Email me</Toggle>
	<input type="hidden" name="notify" value={notify ? 'on' : ''} />

	<ToggleGroup multiple value={tags} onValueChange={(v) => (tags = v)}>
		<ToggleGroupItem value="urgent">Urgent</ToggleGroupItem>
		<ToggleGroupItem value="billing">Billing</ToggleGroupItem>
	</ToggleGroup>
	{#each tags as tag (tag)}<input type="hidden" name="tags" value={tag} />{/each}

	<button>Save</button>
</form>
```

A `Toggle` always renders `type="button"` and ignores `type` and `form`, so it never submits or joins a form by itself. For a file field in a native form, keep the `File[]` from `onFilesAccepted` and post it with `FormData`. `FileUpload`'s internal `<input type="file">` has no `name` attribute.

## Rules

- Pass `isDark` from the parent. None of these six components ever calls `onIsDarkChange`.
- Every component accepts both `class` and `className`. On `ColorPicker`'s `swatch` and `input` variants the class goes on the trigger or field, while extra attributes go on the wrapper.
- `ColorPicker` emits hex (`#rrggbb`, or `#rrggbbaa` when `showAlpha` and alpha is below 1), whatever format the user typed.
- `ToggleGroup` defaults to single-select (`multiple={false}`) and still uses a `string[]` value.
- `onPressedChange` and `onValueChange` get `details`. Call `details.cancel()` to veto the change.

## Parity gaps compared with upstream React (from `src/lib/parity/port-parity.test.ts` and component headers)

- FileSystem: one tree view only. These are not ported: `defaultView`, `view`, `onViewChange`, `loadChildren` (lazy loading), `renderFilePreview`, `loadPreviewImageUrl`, search, sort, filters, back and forward navigation, and the built-in viewer dialog. Port additions are `bind:selectedPath`, `onRename`, and `renamable`.
- FileUpload: `borderBeamTheme` was replaced by `isDark`. The icons are text glyphs.
- FileThumbnail: port addition `pdfUrl`, `pdfFile`, `pageNumber`, `width` for built-in PDF rendering.
- GroupText: no `render` prop. It always renders a `div`.
- ToggleGroupItem: `className`, `variant`, and `size` are typed and forwarded, but the ledger records them as unconfirmed parity gaps.
- ColorPicker: the popover renders inline (no portal), the format picker is a native `<select>`, and the per-channel copy buttons and alpha scrub-dragging are missing.
