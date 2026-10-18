# Virtual list

The shared windowing component behind PDF pages, sheet rows, slide lists, DOCX thumbnails, layout blocks and review grids. Use it for any long list in an app built on the library.

## Imports

- npm root: `import { VirtualList, computeWindow, DEFAULT_OVERSCAN } from 'extend-ui-svelte';`
- Copy-in (`virtual-list` item): `$lib/extend-ui/virtual-list/index.js` also exports `computeVariableWindow`, `offsetTopForIndex`, `prefixOffsets`, `totalHeight`, and the types `VirtualWindow`, `VirtualWindowOptions`, `VariableWindowOptions`.

## `VirtualList` props (`generics="T"`)

| Prop | Type | Notes |
|---|---|---|
| `items` | `T[]` | Required. Only the visible window renders. |
| `height` | `number` | Required. Viewport height in px. |
| `itemHeight` | `number` | Fixed row height in px (fixed mode). Ignored when `estimateSize` is set. |
| `estimateSize` | `(index: number) => number` | Turns on measured mode: rows size to content and a `ResizeObserver` replaces estimates with real heights. |
| `overscan` | `number` | Extra rows above and below. Default `DEFAULT_OVERSCAN` = 3. |
| `tabindex` | `number \| null` | Default 0 (scroll region is focusable). Pass `null` when the parent owns keyboard navigation. |
| `children` | `Snippet<[T, number]>` | Row content, called with the item and its index. |

```svelte
<script lang="ts">
	import { VirtualList } from 'extend-ui-svelte';

	type Row = { id: string; label: string };
	let rows = $state.raw<Row[]>(
		Array.from({ length: 50_000 }, (_, i) => ({ id: String(i), label: `Row ${i + 1}` }))
	);
</script>

<VirtualList items={rows} itemHeight={32} height={480}>
	{#snippet children(row, index)}
		<div class="row">{index + 1}. {row.label}</div>
	{/snippet}
</VirtualList>
```

Measured mode:

```svelte
<VirtualList items={notes} estimateSize={() => 72} height={600}>
	{#snippet children(note)}
		<article>{note.body}</article>
	{/snippet}
</VirtualList>
```

## Behavior to know

- Each row is absolutely positioned inside a spacer. Do not rely on normal document flow between rows or on `:nth-child` for zebra striping; use the index instead.
- Measured heights are keyed by item identity. Reassigning an array that contains the same objects keeps measurements. Equal primitive items (two identical strings) share one measurement, so pass objects when that matters.
- When a row above the viewport changes height in measured mode, the list adjusts `scrollTop` to keep visible content still.
- A hidden list (for example in a closed tab) reports 0 heights; the list keeps the last good size.
- Keep `items` in `$state.raw` and update by reassignment.

## Pure helpers (`window.ts`)

- `computeWindow({ itemCount, itemHeight, viewportHeight, scrollTop, overscan? }): { start, end }` returns a half-open range and clamps `scrollTop`.
- `prefixOffsets(sizes: number[]): number[]` where `offsets[i]` is the top of row `i` and `offsets[n]` is the total height.
- `computeVariableWindow({ offsets, viewportHeight, scrollTop, overscan? })` does the same for variable heights (binary search).
- `totalHeight(itemCount, itemHeight)` and `offsetTopForIndex(index, itemHeight)`.

Use these to build a custom virtualized grid without the component.
