# DocumentSplits reference

Groups the pages of one PDF into named, ordered sections (for example one upload holding an invoice, a bill of lading, and a W-9). Source: `src/lib/components/document-splits/DocumentSplits.svelte`, `splits.ts`.

```ts
import { DocumentSplits } from 'extend-ui-svelte';
import {
	addSplit, areSplitGroupsEqual, arrayMove, createInitialSplits, createPageRangeLabel,
	findGroupId, getGroupPages, getPageNumber, INITIAL_SPLITS, movePage, movePageToAdjacentGroup,
	movePageToGroup, nextSplitId, removeSplit, renameSplit, reorderPageInGroup, reorderSplits,
	splitGroup,
	type DocumentSplit, type DocumentSplitPageId
} from 'extend-ui-svelte/components/document-splits';
// Registry copy-in: '$lib/components/document-splits/index.js'
// (registry deps: dark-mode, engines, file-thumbnail)
```

## Props

| Prop | Type | Default | Bindable | Description |
|---|---|---|---|---|
| `splits` | `DocumentSplit[]` | required | no | Controlled split groups. |
| `activePage` | `number` | required | no | 1-based page highlighted with `aria-current`; `0` for none. |
| `onSelectPage` | `(pageNumber: number) => void` | required | - | Called with the 1-based page number when a thumbnail is clicked. |
| `onSplitsChange` | `(splits: DocumentSplit[]) => void` | required | - | Called with the next array after every edit. Skipped when the edit is a no-op (`areSplitGroupsEqual`). |
| `thumbnailImages` | `Record<DocumentSplitPageId, string>` | `{}` | no | Cached image URLs per page id (e.g. data URLs). Wins over `pdfUrl` renders. |
| `pdfUrl` | `string \| null` | `null` | no | PDF rendered into thumbnails lazily (IntersectionObserver), loaded once per URL, client-only. |
| `withFrameDivider` | `boolean` | `true` | no | Shows the frame divider border. |
| `isDark` | `boolean` | `false` | no | Parent-controlled dark mode. |
| `onIsDarkChange` | `(isDark: boolean) => void` | - | - | Accepted for parity; never called. |
| `class` / `className` | `string` | - | no | Merged onto the root. |

No snippets, no `$bindable` props. The component never mutates `splits`; if you do not assign the value from `onSplitsChange`, the UI does not change.

## Types

```ts
/** Page identifier, 1-based: 'page-1', 'page-2', ... */
type DocumentSplitPageId = `page-${number}`;

type DocumentSplit = {
	id: string;
	title: string;
	pages: DocumentSplitPageId[]; // ordered; may be non-contiguous; may be empty
};
```

## Pure helpers (all return new arrays, never mutate)

| Helper | Signature | Behavior |
|---|---|---|
| `createInitialSplits` | `(pageCount: number) => DocumentSplit[]` | Up to three groups titled `Page N` / `Pages A-B`. **`pageCount <= 0` returns the 10-page demo `INITIAL_SPLITS`.** |
| `getPageNumber` | `(pageId) => number` | `'page-7'` to `7`. |
| `createPageRangeLabel` | `(pageIds) => string` | `'Pages 1, 2, 5'` or `'No pages'`. |
| `addSplit` | `(groups) => DocumentSplit[]` | Appends empty `Split N`. |
| `removeSplit` | `(groups, groupId) => DocumentSplit[]` | Drops the group **and its pages**. Keeps the last group. |
| `renameSplit` | `(groups, groupId, title)` | |
| `splitGroup` | `(groups, groupId, atIndex?)` | Cuts at `atIndex` (default midpoint, extra page in first half). Second half is `<title> (2)` with a new id. No-op for <2 pages. |
| `reorderSplits` | `(groups, fromIndex, toIndex)` | |
| `movePage` | `(groups, pageId, direction: -1 \| 1)` | Within its group. |
| `movePageToAdjacentGroup` | `(groups, pageId, direction: -1 \| 1)` | Appends to previous/next group. |
| `movePageToGroup` | `({ draggedPageId, groups, insertIndex, targetGroupId })` | |
| `reorderPageInGroup` | `({ draggedPageId, groups, overPageId })` | |
| `findGroupId` | `(groups, id) => string \| null` | Accepts a group id or page id. |
| `getGroupPages` | `(groups, groupId) => DocumentSplitPageId[]` | |
| `areSplitGroupsEqual` | `(a, b) => boolean` | Deep compare. |
| `nextSplitId` | `(groups) => string` | Strictly increasing `split-<timestamp>`. |
| `arrayMove` | `<T>(items, from, to) => T[]` | |

Use these in your own toolbar (e.g. "Auto-split by classifier") and pass the result back as `splits`.

## Controls and keyboard

Every drag action has a button equivalent, so the component is fully keyboard operable with Tab and Enter/Space:

- Header: "Add split" button.
- Per split: drag handle (`Reorder <title>`), title text input (rename), page count, `Move <title> up` / `down`, `Split <title> in two` (disabled under 2 pages), `Remove <title>` (disabled for the last split).
- Per page: thumbnail button `Select page N` (calls `onSelectPage`), plus `Move page N left` / `right`, `Move page N to previous split` / `next split`.
- Native HTML5 drag: drag pages within or across splits (drop on a page or the split's drop zone), drag split handles to reorder splits.

## Full example: split review beside the PDF

```svelte
<script lang="ts">
	import { DocumentSplits, PdfViewer } from 'extend-ui-svelte';
	import {
		createInitialSplits,
		getPageNumber,
		type DocumentSplit
	} from 'extend-ui-svelte/components/document-splits';

	const PDF_URL = '/uploads/packet-4821.pdf';

	// From your classifier: 1-based inclusive page ranges.
	const predicted = [
		{ title: 'Invoice', start: 1, end: 2 },
		{ title: 'Bill of lading', start: 3, end: 3 },
		{ title: 'W-9', start: 4, end: 5 }
	];

	let splits = $state<DocumentSplit[]>(
		predicted.map((p, i) => ({
			id: `split-${i + 1}`,
			title: p.title,
			pages: Array.from({ length: p.end - p.start + 1 }, (_, k) => `page-${p.start + k}` as const)
		}))
	);
	let activePage = $state(1);

	// Back to ranges for the API. Pages can be reordered or non-contiguous after edits.
	const payload = $derived(
		splits.map((s) => ({ title: s.title, pages: s.pages.map(getPageNumber) }))
	);

	// No classifier output? Use createInitialSplits(pageCount) once the PDF reports its page count.
	function onLoaded(pageCount: number) {
		if (splits.length === 0) splits = createInitialSplits(pageCount);
	}
</script>

<div class="grid">
	<DocumentSplits
		{splits}
		{activePage}
		pdfUrl={PDF_URL}
		onSelectPage={(n) => (activePage = n)}
		onSplitsChange={(next) => (splits = next)}
	/>
	<PdfViewer src={PDF_URL} height={720} onDocumentLoadSuccess={onLoaded} onActivePageChange={(n) => (activePage = n)} />
</div>

<pre>{JSON.stringify(payload, null, 2)}</pre>

<style>
	.grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; }
</style>
```

`PdfViewer` has no prop to scroll to a page from the outside, so clicking a thumbnail updates `activePage` but does not move the viewer. See `../../extend-ui-viewers/SKILL.md` for what the viewer exposes.

## Gotchas

- Page ids are 1-based strings. Do not use 0-based indexes, and do not use plain numbers in `pages`.
- `createInitialSplits(0)` returns demo data for a 10-page paper. Wait for the real page count first, or build splits from your own data.
- Removing a split also removes its pages from every split. If you need "every page belongs somewhere", move the pages first (`movePageToAdjacentGroup`) or check page coverage before you save.
- Empty splits are allowed (after `addSplit`). Filter them out before saving if your backend rejects them.
- `thumbnailImages` keys must be `page-N` ids. A page with neither an image nor `pdfUrl` shows a placeholder thumbnail.
- The `pdfUrl` engine loads in the browser only, so SSR is safe (see the core skill for engine setup).
- Package users cannot import the PDF engine directly (it is not exported from `extend-ui-svelte`). Get the page count from `PdfViewer`'s `onDocumentLoadSuccess` or your backend. Registry users can import `$lib/engines/pdf/index.js`.

## Differences from upstream (deliberate)

dnd-kit replaced by native drag and drop plus button controls for every move; `class` accepted alongside `className`; added rename input, "Split in two", and a rendered `activePage` highlight (upstream documents it but never renders it); `pdfUrl` thumbnails via FileThumbnail; dark mode via `isDark` only. The parity suite records no unrecorded props.
