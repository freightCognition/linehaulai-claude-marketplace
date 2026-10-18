---
name: extend-ui-extraction
description: This skill should be used when the user asks to build an extraction schema editor or JSON schema builder, split a multi-document PDF into sections or document splits, show parsed OCR layout blocks, show extracted values with citations or bounding boxes on a PDF, build a human review or document review UI, highlight the source region of an extracted field, compare actual vs expected extraction output, or otherwise build a document-AI / extraction-review screen with the extend-ui-svelte Svelte 5 library (SchemaBuilder, SchemaBuilderPanel, SchemaJsonView, DocumentSplits, LayoutBlocks, OcrBlocksPanel, BoundingBoxCitations, HumanReviewBlock, HumanReviewPanel).
---

# extend-ui-svelte: extraction and review components

Use this skill for the four document-AI components of `extend-ui-svelte` (Svelte 5 port of extend-hq/ui): `SchemaBuilder`, `DocumentSplits`, `LayoutBlocks`, and `BoundingBoxCitations` (with `HumanReviewPanel`). For install, SSR, dark mode, and the PDF engine, read `../extend-ui-svelte/SKILL.md` first. For `PdfViewer` props and its `pageOverlay` snippet, read `../extend-ui-viewers/SKILL.md`.

## Where each one fits in a document-processing app

| Step | Component | Job |
|---|---|---|
| Configure | `SchemaBuilder` | Let a user define the fields to extract; emits a JSON schema. |
| Classify / split | `DocumentSplits` | Group the pages of one uploaded PDF into named sections (invoice, W-9, contract). |
| Parse | `LayoutBlocks` | Show OCR output as a virtualized list of typed blocks (heading, table, figure...). |
| Review | `BoundingBoxCitations` | PDF on the left, editable extracted fields on the right; focusing a field highlights and scrolls to its bounding box. |

## Imports

Root entry exports the components only. Import helpers and data types from the component subpath.

```ts
import { SchemaBuilder, DocumentSplits, LayoutBlocks, BoundingBoxCitations, HumanReviewPanel } from 'extend-ui-svelte';
import { serializeSchema, type SchemaBuilderSchema } from 'extend-ui-svelte/components/schema-builder';
import { createInitialSplits, getPageNumber, type DocumentSplit } from 'extend-ui-svelte/components/document-splits';
import { getOcrBlocks, blockToArea, type OcrBlock, type ParsedOcrOutput } from 'extend-ui-svelte/components/layout-blocks';
import { type ReviewField, type ReviewMetadataEntry } from 'extend-ui-svelte/components/bounding-box-citations';
```

Registry copy-in (no registry URL is published yet; follow `../extend-ui-svelte/references/installation.md` or run `/extend-ui-svelte:add-component <name>`) puts the same files under `$lib/components/<name>/`; import from `$lib/components/<name>/index.js` with identical names.

Upstream React names are kept as aliases: `SchemaBuilderPanel`, `OcrBlocksPanel`, `HumanReviewBlock` (= `BoundingBoxCitations`). All four accept both `class` and `className` and take parent-controlled `isDark`.

## Data shapes to get right

**Schema** (`SchemaBuilderSchema`): an editor model, not JSON Schema. Each property needs a stable `id` plus `key`, `type` (`string | number | integer | boolean | null | object | array | enum`), and `description`; nested `properties`, `items`, `enumValues`. Call `serializeSchema(schema)` (or listen to `onSerializedSchemaChange`) to get `{ type: 'object', properties, required? }` JSON Schema. Enums serialize as `type: 'string'` + `enum` + `enumDescriptions`. Properties with a blank key are dropped.

**Splits** (`DocumentSplit[]`): `{ id, title, pages }` where `pages` are strings `` `page-${n}` `` and **n is 1-based**. Pages inside a split can be non-contiguous and reordered; use `getPageNumber(pageId)` to convert. `activePage` and `onSelectPage` also use 1-based numbers (0 = none).

**Layout blocks** (`OcrBlock`): `getOcrBlocks(parsedOutput)` flattens `{ chunks: [{ blocks: ParsedOcrBlock[] }] }`. Geometry (`boundingBox` `{left, top, right, bottom}` or `polygon` `[{x, y}]`) is in the **same units as `metadata.page.width/height`** (pixels or points, whatever your OCR emits). `page` is 1-based. `blockToHighlightArea(block)` converts to **percent of page** (0–100).

**Citations** (`ReviewField`): `{ key, schema, actual, expected, location?, metadataPath? }`. `location` is `{ page, area: { left, top, width, height } }` with `page` 1-based and `area` in **percent 0–100** (not pixels, not 0–1). Alternatively pass `metadata: Record<path, { citations: [{ page, polygon, pageWidth, pageHeight }] }>` where `polygon` is in page units (PDF points, e.g. 612×792); the component converts it with `getCitationLocation`. Inline `location` wins over metadata.

## Minimal examples

```svelte
<script lang="ts">
	import { SchemaBuilder } from 'extend-ui-svelte';
	import type { SchemaBuilderSchema, SerializedSchema } from 'extend-ui-svelte/components/schema-builder';

	let schema = $state<SchemaBuilderSchema>({
		properties: [{ id: 'f1', key: 'invoice_number', type: 'string', description: 'Invoice ID', required: true }]
	});
	let jsonSchema = $state<SerializedSchema>();
</script>

<SchemaBuilder {schema} onSchemaChange={(s) => (schema = s)} onSerializedSchemaChange={(j) => (jsonSchema = j)} />
```

```svelte
<script lang="ts">
	import { DocumentSplits } from 'extend-ui-svelte';
	import { createInitialSplits, type DocumentSplit } from 'extend-ui-svelte/components/document-splits';

	let splits = $state<DocumentSplit[]>(createInitialSplits(9));
	let activePage = $state(1);
</script>

<DocumentSplits {splits} {activePage} pdfUrl="/upload.pdf"
	onSelectPage={(n) => (activePage = n)} onSplitsChange={(next) => (splits = next)} />
```

```svelte
<script lang="ts">
	import { LayoutBlocks } from 'extend-ui-svelte';
	import { getOcrBlocks, type ParsedOcrOutput } from 'extend-ui-svelte/components/layout-blocks';
	let { output }: { output: ParsedOcrOutput } = $props();
	const blocks = $derived(getOcrBlocks(output));
</script>

<LayoutBlocks {blocks} height={600} onBlockFocus={(b) => console.log(b.page, b.id)} />
```

```svelte
<script lang="ts">
	import { BoundingBoxCitations } from 'extend-ui-svelte';
	import type { JsonObject, ReviewField } from 'extend-ui-svelte/components/bounding-box-citations';

	const fields: ReviewField[] = [
		{ key: 'total', schema: { type: 'number', title: 'Total' }, actual: 1280.5, expected: 1280.5,
		  location: { page: 1, area: { left: 62, top: 78, width: 24, height: 3 } } }
	];
	let values = $state<JsonObject>();
	let activeFieldKey = $state<string | null>(null);
</script>

<BoundingBoxCitations src="/invoice.pdf" {fields} bind:values bind:activeFieldKey height={720} />
```

## Flagship flow: the extraction review screen

`BoundingBoxCitations` already is "PDF viewer + citations side by side". Use it rather than composing by hand:

1. Map your extraction API output to `ReviewField[]` once (keep the array reference stable; a new `fields` array resets all edits).
2. Supply locations: inline `location` per field, or pass the API's `metadata` (citations with polygons) and set `metadataPath` per field. Array rows resolve to `` `${metadataPath}[${row}]` `` by default; override with `resolveArrayItemMetadataPath`.
3. `bind:activeFieldKey` to read the focused field or move the highlight (dotted keys for nested objects, e.g. `vendor.address`). Setting it from outside moves the highlight but does not scroll the PDF; to jump from your own UI, focus the card element `[data-review-field="<key>"]` (see the example). Focusing a field card (keyboard focus, click, or hover) makes it active, smooth-scrolls the PDF to the box, and draws the blue highlight; hovering an array cell previews its row's box; clicking a faint box on the page focuses that field.
4. `bind:values` holds the reviewer's corrected output keyed by top-level field key. Submit it on approve. Set `showExpected={false}` for a read-only "extracted values + citations" view.
5. Handle `onFieldFocus` / `onActiveFieldChange` for analytics or a URL hash, and `onLocationHover` for custom previews.

Full mock-data screen: `examples/extraction-review.svelte`.

Custom layouts are possible with `PdfViewer` + `HumanReviewPanel` + `HumanReviewHighlight` + `boxesForPage` in a `pageOverlay` snippet, but `PdfViewer` exposes no scroll-to-area handle, so you lose the jump-to-box behavior. Prefer the block.

## Intake flow: splits plus layout blocks on the page

Run `DocumentSplits` next to a `PdfViewer` (shared 1-based page numbers), then show `LayoutBlocks` for the chosen page and draw the focused block on the page via `pageOverlay` + `blockToArea(block, { width: overlay.pageWidth, height: overlay.pageHeight })`. The port does not ship upstream's `OcrBlockOverlay`, so this overlay is yours to render. See `examples/document-intake.svelte`.

## Rules

- Treat `DocumentSplits` as fully controlled: update `splits` in `onSplitsChange` or nothing changes. `SchemaBuilder` is controlled when `schema` is passed, otherwise uncontrolled from `defaultSchema`.
- Omitting data shows upstream demo content: `SchemaBuilder` defaults to `SAMPLE_SCHEMA`, `BoundingBoxCitations`/`HumanReviewPanel` default to `REVIEW_FIELDS` (bank statement), and `createInitialSplits(0)` returns the 10-page `INITIAL_SPLITS`. Always pass real data.
- Never convert coordinates to 0–1. Review areas and highlight areas are percentages.
- If citations come from the source document but the viewer shows a split, remap `page` to the split's local page numbers before passing fields.
- `HumanReviewPanel` height comes from the CSS variable `--human-review-panel-height` (default 560px); `BoundingBoxCitations` sets it to fill and uses `height` (default 600) for the PDF viewport.

## References

- `references/schema-builder.md`: props, types, helpers, serialization rules.
- `references/document-splits.md`: props, pure split helpers, keyboard controls, page export.
- `references/layout-blocks.md`: OCR types, block-type mapping, coordinate math, overlays.
- `references/bounding-box-citations.md`: block and panel props, citation types, helpers, keyboard, gotchas.
- `examples/extraction-review.svelte`, `examples/document-intake.svelte`.

## Parity with upstream React

`src/lib/parity/port-parity.test.ts` records no unrecorded prop gaps for these four components; every deviation is deliberate and listed in each reference file. Main ones: `theme` is replaced by `isDark` on the review components (SchemaBuilder still accepts `theme`); SchemaBuilder shows form and JSON side by side, drags top-level fields only, and adds `required`; DocumentSplits uses native drag and drop plus button controls; LayoutBlocks has no `OcrBlockOverlay`; the review grid is a DOM table with single-cell selection and the JSON diff is line-level only.
