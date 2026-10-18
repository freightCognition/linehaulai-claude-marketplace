# LayoutBlocks reference

Virtualized list of parsed OCR layout blocks (headings, paragraphs, lists, tables, figures, headers, footers, page numbers) with sanitized markdown, a type badge, confidence, and page number per row. Source: `src/lib/components/layout-blocks/LayoutBlocks.svelte`, `layout-blocks.ts`.

```ts
import { LayoutBlocks, OcrBlocksPanel } from 'extend-ui-svelte';
import {
	getOcrBlocks, blockToHighlightArea, blockToArea, renderBlockMarkdown, estimateOcrBlockRowHeight,
	OCR_BLOCK_TYPE_LABELS, DEFAULT_LAYOUT_BLOCKS_HEIGHT, DEFAULT_LAYOUT_BLOCKS_OVERSCAN,
	type OcrBlock, type OcrBlockType, type ParsedOcrBlock, type ParsedOcrOutput,
	type BoundingBox, type HighlightArea, type Point, type LayoutBlocksProps
} from 'extend-ui-svelte/components/layout-blocks';
// Registry copy-in: '$lib/components/layout-blocks/index.js'
// (registry deps: dark-mode, virtual-list; npm: marked, hast-util-sanitize, hast-util-from-html, hast-util-to-html)
```

`OcrBlocksPanel` is the upstream name for the same component.

## Props

| Prop | Type | Default | Bindable | Description |
|---|---|---|---|---|
| `blocks` | `OcrBlock[]` | required | no | Rows to render. Build with `getOcrBlocks`. |
| `activeBlockId` | `string` | `undefined` | no | Controlled focused block. When unset, focus is local and starts on the first block. |
| `onBlockFocus` | `(block: OcrBlock) => void` | - | - | Called once each time a different block gains focus (hover, keyboard focus, or click). |
| `height` | `number` | `420` | no | Scroll viewport height in px. |
| `overscan` | `number` | `6` | no | Extra rows rendered above and below the viewport. |
| `isDark` | `boolean` | `false` | no | Parent-controlled dark mode (adds `dark` class). |
| `onIsDarkChange` | `(isDark: boolean) => void` | - | - | Accepted for parity; never called. |
| `class` / `className` | `string` | - | no | Merged onto the root `<aside>`. |

No snippets. Empty `blocks` renders "No layout blocks found."

## Types

```ts
type Point = { x: number; y: number };
type BoundingBox = { left: number; top: number; right: number; bottom: number };

type OcrBlockType =
	| 'heading' | 'paragraph' | 'list' | 'table' | 'figure' | 'header' | 'footer' | 'page_number';

/** Raw block as returned by the parser. */
type ParsedOcrBlock = {
	id: string;
	type: string;      // 'heading' | 'section_heading' | 'text' | 'table' | 'figure' | 'image' | 'header' | 'footer' | 'page_number' | ...
	content: string;   // markdown / limited HTML
	metadata: {
		page: { number: number; width: number; height: number };
		layoutClass?: string;        // 'List Item' turns a block into a list
		minOcrConfidence?: number;   // 0-1
		avgOcrConfidence?: number;   // 0-1
	};
	polygon?: Point[];
	boundingBox?: BoundingBox;
};

type ParsedOcrOutput = { chunks: { blocks: ParsedOcrBlock[] }[] };

/** Renderable block. */
type OcrBlock = {
	id: string;
	type: OcrBlockType;
	text: string;
	page: number;        // 1-based, from metadata.page.number
	pageWidth: number;   // same units as the geometry
	pageHeight: number;
	confidence: number;  // 0-1, shown as a rounded percent
	polygon?: Point[];
	boundingBox?: BoundingBox;
};

/** Percent of the page, 0-100. */
type HighlightArea = { left: number; top: number; width: number; height: number };
```

## `getOcrBlocks` mapping

| Raw `type` / condition | `OcrBlockType` |
|---|---|
| `heading`, `section_heading` | `heading` |
| `header` / `footer` / `page_number` | same |
| `figure`, `image` | `figure` |
| `table` | `table` |
| `metadata.layoutClass === 'List Item'` (any other type) | `list` |
| `text` | `paragraph` |
| anything else | dropped |

Blocks with `page.width <= 0` or `page.height <= 0` are dropped. `confidence` = `avgOcrConfidence ?? minOcrConfidence ?? 1`. Build `OcrBlock` objects by hand if your parser has a different shape.

## Coordinate helpers

- `blockToHighlightArea(block, pageSize?)`: uses `boundingBox`, or the min/max of `polygon`, divided by `pageWidth`/`pageHeight`, times 100. Returns percentages.
- `blockToArea(block, pageSize?)`: same, as a CSS string `left:..%;top:..%;width:..%;height:..%;` for a `style` attribute.
- `pageSize` (`{ width, height }` of the page as rendered) fixes orientation mismatches: if the block's page is landscape but the rendered page is portrait, the area is rotated 90 degrees (and the reverse for 270). With no `pageSize`, a landscape block page is always rotated. Pass the PdfViewer overlay's `pageWidth`/`pageHeight` to avoid surprises.
- A block with neither `boundingBox` nor `polygon` yields `Infinity`/`NaN` values. Check before drawing.

## Other exports

`renderBlockMarkdown(text)` returns sanitized HTML (GFM via marked, `<caption>` rewritten to `<figcaption>`, sanitized with GitHub's schema plus `figure`, `figcaption`, `caption`). It is framework-free, so it is SSR safe. `estimateOcrBlockRowHeight(block)`, `OCR_BLOCK_TYPE_LABELS`, `DEFAULT_LAYOUT_BLOCKS_HEIGHT` (420), `DEFAULT_LAYOUT_BLOCKS_OVERSCAN` (6).

## Keyboard and focus

Each row is a `<button>`: Tab moves through rendered rows, and focusing, hovering, or clicking a row makes it active (`data-active`, `.active`) and calls `onBlockFocus`. Rows outside the virtual window are not in the DOM, so Tab only reaches nearby rows. There are no arrow-key bindings.

## Full example: blocks list linked to the PDF page

Upstream's `OcrBlockOverlay` is not ported, so draw the overlay yourself with `PdfViewer`'s `pageOverlay` snippet.

```svelte
<script lang="ts">
	import { LayoutBlocks, PdfViewer } from 'extend-ui-svelte';
	import {
		blockToArea,
		getOcrBlocks,
		type OcrBlock,
		type ParsedOcrOutput
	} from 'extend-ui-svelte/components/layout-blocks';

	const output: ParsedOcrOutput = {
		chunks: [
			{
				blocks: [
					{
						id: 'b1', type: 'section_heading', content: '## Bill To',
						metadata: { page: { number: 1, width: 612, height: 792 }, avgOcrConfidence: 0.99 },
						boundingBox: { left: 48, top: 140, right: 200, bottom: 160 }
					},
					{
						id: 'b2', type: 'table', content: '| Item | Qty | Amount |\n|---|---|---|\n| Freight | 1 | 1,200.00 |',
						metadata: { page: { number: 1, width: 612, height: 792 }, avgOcrConfidence: 0.95 },
						polygon: [ { x: 48, y: 300 }, { x: 564, y: 300 }, { x: 564, y: 380 }, { x: 48, y: 380 } ]
					}
				]
			}
		]
	};

	const blocks = getOcrBlocks(output);
	let active = $state<OcrBlock | undefined>(blocks[0]);
</script>

<div class="grid">
	<PdfViewer src="/invoice.pdf" height={640}>
		{#snippet pageOverlay(overlay)}
			{#if active && active.page === overlay.pageNumber}
				<div
					class="block-box"
					style={blockToArea(active, { width: overlay.pageWidth, height: overlay.pageHeight })}
				></div>
			{/if}
		{/snippet}
	</PdfViewer>
	<LayoutBlocks {blocks} activeBlockId={active?.id} height={640} onBlockFocus={(b) => (active = b)} />
</div>

<style>
	.grid { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 1rem; }
	.block-box {
		position: absolute;
		box-sizing: border-box;
		border: 2px solid rgb(234 88 12 / 0.8);
		background: rgb(234 88 12 / 0.1);
		pointer-events: none; /* the overlay layer already disables pointer events */
	}
</style>
```

## Gotchas

- Geometry units must match `metadata.page.width/height`. Mixing PDF points (612×792) with pixel geometry (for example 1275×1651 at 150 DPI) misplaces every box.
- `page` is 1-based, matching `PdfViewer`'s `overlay.pageNumber`.
- Controlled `activeBlockId` is not reset by the panel; `onBlockFocus` still fires for each new block, and you decide whether to accept it.
- In uncontrolled mode, if `blocks` changes and the focused block disappears, focus resets to the new first block.
- Hover changes focus, so a mouse moving across the list fires `onBlockFocus` repeatedly. Debounce expensive work (like scrolling a viewer).
- `blockToArea` returns a CSS string, not an object (unlike upstream's React style object).
- Children of `pageOverlay` need `position: absolute`. The overlay layer is sized to the unrotated page and rotates with it.

## Differences from upstream (deliberate)

Virtualization uses the shared measured VirtualList instead of @tanstack/react-virtual; added `height`/`overscan`; markdown via marked + hast-util-sanitize (same schema as upstream's rehype-sanitize); text badges instead of icons; click also focuses; `OcrBlockOverlay`, `ATTENTION_OCR_OUTPUT`, `PDF_URL`, and the `OcrBlocks` demo are not ported. The parity suite records no unrecorded props.
