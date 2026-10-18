# FileSystem

Source: `src/lib/components/file-system/FileSystem.svelte`, `tree.ts`, `types.ts`. A file and folder tree built from a flat manifest, with expand and collapse, selection, keyboard navigation, type-ahead, and inline rename. It does not display file contents. You open the file yourself in `onFileOpen`.

## Imports

```ts
import { FileSystem } from 'extend-ui-svelte';
import {
	FileSystem,
	type FileSystemProps,
	type FileSystemItem,
	type FileSystemFileItem,
	type FileSystemFolderItem,
	type FileSystemEntry,
	type FileEntry,
	type FolderEntry,
	type FileSystemIndex,
	type VisibleRow,
	buildFileSystemIndex,
	flattenVisibleEntries,
	ancestorFolderPaths,
	normalizeFolderPath,
	pathName,
	pathParent
} from 'extend-ui-svelte/components/file-system';
// registry copy-in: '$lib/components/file-system/index.js' (needs $lib/dark-mode)
```

## Props

| Prop | Type | Default | Bindable | Description |
| --- | --- | --- | --- | --- |
| `items` | `FileSystemItem[]` | required | no | Flat manifest. Folders are optional, because missing prefixes are inferred from file paths. Reactive. |
| `title` | `string` | `'Files'` | no | Header `<h2>` text and the tree's `aria-label`. |
| `defaultPath` | `string` | `''` | no | Folder prefix to expand on mount (for example `'invoices/2026/'`). Read once. |
| `selectedPath` | `string \| null` | `null` | **yes** | Path of the selected entry. Folder paths end in `/`. |
| `onSelectionChange` | `(item: FileSystemItem \| null) => void` | none | no | Fires when selection moves to a different entry by click or keyboard. Not fired for re-selecting the same entry, or when the parent sets `selectedPath`. |
| `onFileOpen` | `(file: FileSystemFileItem, url: string \| null) => void` | none | no | Double-click or Enter on a file. `url` = `file.url`, else `await getFileUrl(file)`, else `null` (also `null` if `getFileUrl` throws). |
| `getFileUrl` | `(file: FileSystemFileItem) => string \| Promise<string>` | none | no | Resolve presigned or proxied URLs lazily. Only called on open. |
| `onRename` | `(item: FileSystemItem, name: string) => void` | none | no | An inline rename was committed (trimmed, non-empty, changed). The tree shows the new name locally. |
| `renamable` | `boolean` | `true` | no | Enables F2 rename. |
| `class` / `className` | `string` | `''` | no | Merged onto the root. |
| `isDark` | `boolean` | `false` | no | Dark palette, plus `data-theme` on the root. |
| `onIsDarkChange` | `(isDark: boolean) => void` | none | no | Accepted for parity. Never called. |

There are no snippets. Icons, the header, and the "No files" empty state are fixed.

## Item types

```ts
type FileSystemFolderItem = {
	kind: 'folder';
	path: string;          // "invoices/2026/" (trailing slash added if missing)
	name?: string; parentPath?: string;
	hasChildren?: boolean; // accepted; lazy loading is NOT ported
	createdAt?: string; updatedAt?: string;
};
type FileSystemFileItem = {
	kind: 'file';
	path: string;          // "invoices/2026/jan.pdf"
	key?: string;          // S3/R2 object key, defaults to path
	name?: string; parentPath?: string;
	contentType?: string; size?: number;
	createdAt?: string; updatedAt?: string; etag?: string;
	url?: string;          // public or presigned; else getFileUrl
	previewImageUrl?: string | null; previewImageUrls?: string[] | null;
	previewPageCount?: number; previewAspectRatio?: number; // accepted, not rendered
	metadata?: Record<string, string>;
};
type FileSystemItem = FileSystemFolderItem | FileSystemFileItem;
```

Sorting puts folders first, then sorts by name with `localeCompare`. Root-level paths have no slash, for example `'readme.txt'`.

## Keyboard and accessibility

The tree uses `role="tree"` and each row is a `role="treeitem"` with `aria-selected`, `aria-expanded` (folders), and `aria-level`. A roving tabindex keeps one Tab stop.

| Key | Action |
| --- | --- |
| ArrowDown / ArrowUp | Move to the next or previous visible row **and select it** |
| Home / End | First or last visible row (selects it) |
| ArrowRight | Collapsed folder: expand. Expanded folder: move to its first child |
| ArrowLeft | Expanded folder: collapse. Otherwise: move to the parent folder |
| Enter | Select, then toggle a folder or open a file (`onFileOpen`) |
| F2 | Start inline rename (if `renamable`). In the input, Enter or blur commits and Escape cancels |
| Letters and digits | Finder-style type-ahead (700 ms buffer) |

Mouse: a click selects, a double-click toggles a folder or opens a file, and a click on the chevron toggles without selecting.

## Full example: R2-backed browser with presigned URLs

```svelte
<script lang="ts">
	import { FileSystem } from 'extend-ui-svelte';
	import type { FileSystemItem, FileSystemFileItem } from 'extend-ui-svelte/components/file-system';

	let { items }: { items: FileSystemItem[] } = $props(); // e.g. from +page.server.ts listing the bucket
	let selectedPath = $state<string | null>(null);
	let opened = $state<{ file: FileSystemFileItem; url: string } | null>(null);

	async function presign(file: FileSystemFileItem) {
		const res = await fetch(`/api/files/url?key=${encodeURIComponent(file.key ?? file.path)}`);
		if (!res.ok) throw new Error('presign failed');
		return (await res.json()).url as string;
	}

	async function rename(item: FileSystemItem, name: string) {
		await fetch('/api/files/rename', { method: 'POST', body: JSON.stringify({ path: item.path, name }) });
	}
</script>

<FileSystem
	{items}
	title="Documents"
	defaultPath="invoices/"
	bind:selectedPath
	getFileUrl={presign}
	onFileOpen={(file, url) => (opened = url ? { file, url } : null)}
	onRename={rename}
/>
<p>Selected: {selectedPath ?? 'nothing'}</p>
```

To render `opened` in a viewer, see `examples/file-browser-viewer.svelte` and the extend-ui-viewers skill.

## Gotchas

- Rename is display-only. The tree keeps a local name override keyed by the old path and never changes `items`. If you rewrite `items` with the renamed path, the override for the old path is simply unused.
- Removing the selected item from `items` keeps `selectedPath` unchanged, and `onSelectionChange(null)` does not fire.
- `defaultPath` is read once at mount. Changing it later does nothing.
- `path` must be unique across files and folders, because it is the each-key.
- Paths use `/`. A leading `/` creates an empty-named root folder, so strip it.
- Folders open in place. There is no "navigate into folder" view, breadcrumbs, search, or sort.
- Not ported from upstream: `defaultView`, `view`, `onViewChange`, `loadChildren`, `renderFilePreview`, `loadPreviewImageUrl`, and the built-in viewer dialog. Load the full manifest up front, or build lazy loading on top by appending to `items` when a folder is selected.
