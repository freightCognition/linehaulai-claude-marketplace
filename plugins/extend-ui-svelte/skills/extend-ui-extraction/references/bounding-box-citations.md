# BoundingBoxCitations and HumanReviewPanel reference

Human review of extraction output with source citations. `BoundingBoxCitations` (alias `HumanReviewBlock`) is the full screen: `PdfViewer` on the left, `HumanReviewPanel` on the right, with a resizable split. `HumanReviewPanel` is the right-hand panel on its own. Source: `src/lib/components/bounding-box-citations/`.

```ts
import {
	BoundingBoxCitations, HumanReviewBlock, HumanReviewPanel, HumanReviewHighlight,
	JsonDiffView, JsonCodeView,
	type BoundingBoxCitationsProps, type HumanReviewPanelProps
} from 'extend-ui-svelte';
import {
	boxesForPage, findReviewField, formatCitationValue, getCitationLocation, getMetadataLocation,
	getReviewFieldLocation, getReviewLocationKey, REVIEW_FIELDS,
	type CitationBox, type HighlightArea, type JsonArray, type JsonObject, type JsonPrimitive,
	type JsonValue, type ReviewCitation, type ReviewField, type ReviewFieldSchema,
	type ReviewLocation, type ReviewMetadataEntry, type SchemaPropertyType,
	type ArrayNestedView, type ArrayReviewSide
} from 'extend-ui-svelte/components/bounding-box-citations';
// Registry copy-in: '$lib/components/bounding-box-citations/index.js'
// (registry deps: pdf-viewer, utils, virtual-list)
```

## BoundingBoxCitations props

| Prop | Type | Default | Bindable | Description |
|---|---|---|---|---|
| `src` | `string` | `undefined` | no | PDF URL. Empty shows the viewer's upload prompt. |
| `file` | `string` | `undefined` | no | Upstream alias for `src` (`src` wins). |
| `fileName` | `string` | `undefined` | no | Download file name. |
| `fields` | `ReviewField[]` | `REVIEW_FIELDS` (demo) | no | Fields to review. A new array reference resets `values`. |
| `values` | `JsonObject` | each field's `expected` | **yes** | Reviewer-edited output keyed by top-level `field.key`. |
| `activeFieldKey` | `string \| null` | first field's key | **yes** | Focused field. Nested object properties use dotted keys (`vendor.address`). Unknown keys fall back to the first field. |
| `onFieldFocus` | `(field: ReviewField) => void` | - | - | Fires when a different field becomes active. |
| `onActiveFieldChange` | `(fieldKey: string \| null) => void` | - | - | Fires with the new key. |
| `onLocationHover` | `(location?: ReviewLocation) => void` | - | - | Hovered field or array cell location; `undefined` on leave. |
| `metadata` | `Record<string, ReviewMetadataEntry>` | `undefined` | no | Citation metadata keyed by metadata path (`total`, `line_items[0]`, `vendor.name`). |
| `resolveArrayItemMetadataPath` | `(metadataPath: string, rowIndex: number, rowValue: JsonValue) => string \| undefined` | `` `${path}[${row}]` `` | no | Maps an array row to its metadata path (useful when rows were reordered or edited). |
| `resolveLocation` | `(metadataPath: string) => ReviewLocation \| undefined` | - | no | Custom resolver; tried before `metadata`. |
| `showExpected` | `boolean` | `true` | no | Shows editable expected values, undo, Set to NULL, and the JSON diff. `false` gives a read-only actual-values view. |
| `isDark` | `boolean` | `false` | no | Parent-controlled dark mode. |
| `onIsDarkChange` | `(isDark: boolean) => void` | - | - | Passed to the PdfViewer. |
| `height` | `number` | `600` | no | PDF viewport height in px. |
| `class` / `className` | `string` | `''` | no | Merged onto the root. |

## HumanReviewPanel props

Same meaning as above unless noted.

| Prop | Type | Default | Bindable |
|---|---|---|---|
| `fields` | `ReviewField[]` | `REVIEW_FIELDS` | no |
| `values` | `JsonObject` | each field's `expected` | **yes** |
| `activeFieldKey` | `string` | `undefined` | no (display only; the panel does not set it) |
| `onFieldFocus` | `(field: ReviewField) => void` | - | - |
| `onLocationHover` | `(location?: ReviewLocation) => void` | - | - |
| `resolveArrayItemMetadataPath` | as above | - | no |
| `resolveLocation` | `(metadataPath: string) => ReviewLocation \| undefined` | - | no |
| `showExpected` | `boolean` | `true` | no |
| `isDark` / `onIsDarkChange` | `boolean` / callback (never called) | `false` | no |
| `class` / `className` | `string` | `''` | no |

The panel has no `metadata` prop; pass `resolveLocation={(p) => getMetadataLocation(metadata, p)}`. Height comes from the CSS variable `--human-review-panel-height` (default `560px`).

## Other components

- `HumanReviewHighlight`: `{ location: ReviewLocation }`. The blue box, absolutely positioned in percent. Put it inside a `PdfViewer` `pageOverlay`.
- `JsonDiffView`: `{ actual: JsonObject; expected: JsonObject; isDark?; onIsDarkChange? }`. Split line diff.
- `JsonCodeView`: `{ value: JsonValue; name?: string = 'actual.json'; isDark?; onIsDarkChange? }`.

None of the components take snippets.

## Types

```ts
type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonObject | JsonArray;
type JsonObject = { [key: string]: JsonValue };
type JsonArray = JsonValue[];
type SchemaPropertyType = 'string' | 'number' | 'integer' | 'boolean' | 'object' | 'array';

interface ReviewFieldSchema {
	type: SchemaPropertyType;
	title?: string;            // card heading; falls back to key
	description?: string;
	enum?: Array<string | number>;  // renders a select
	properties?: Record<string, ReviewFieldSchema>;  // object: nested cards
	items?: ReviewFieldSchema;                        // array: grid columns
}

/** Percent of the page, 0-100. */
interface HighlightArea { left: number; top: number; width: number; height: number; }

/** page is 1-based. */
interface ReviewLocation { page: number; area: HighlightArea; }

interface ReviewField {
	key: string;
	schema: ReviewFieldSchema;
	actual: JsonValue;      // model output
	expected: JsonValue;    // starting value for the editable side
	location?: ReviewLocation;   // wins over metadata
	metadataPath?: string;       // defaults to key
}

/** Polygon in page units (e.g. PDF points); page is 1-based. */
interface ReviewCitation {
	page: number;
	polygon?: Array<{ x: number; y: number }>;
	pageWidth: number;
	pageHeight: number;
}

interface ReviewMetadataEntry { citations?: ReviewCitation[]; }

interface CitationBox { field: ReviewField; location: ReviewLocation; }

interface ArrayNestedView { rowIndex: number; columnId: string; title: string; schema: ReviewFieldSchema; value: JsonValue; }
type ArrayReviewSide = 'actual' | 'expected';
```

Note: `ReviewFieldSchema` has no `null` or `enum` type. `serializeSchema` from SchemaBuilder emits enums as `{ type: 'string', enum: [...] }`, which `ReviewFieldSchema` accepts, but `SerializedSchemaProperty.type` is typed `string`, so map it yourself (cast after checking the type, drop or handle `null` fields, and add `title` if you want friendly card headings).

## Location resolution order

For a field: `field.location` first, then `resolveLocation(metadataPath ?? key)`, then `getMetadataLocation(metadata, metadataPath ?? key)`, which takes the first citation with a non-empty polygon and converts it with `getCitationLocation`:

```
left   = min(x) / pageWidth  * 100
top    = min(y) / pageHeight * 100
width  = (max(x) - min(x)) / pageWidth  * 100
height = (max(y) - min(y)) / pageHeight * 100
```

Nested object properties resolve at `` `${parentPath}.${prop}` ``. Array rows resolve at `` `${path}[${row}]` `` or your `resolveArrayItemMetadataPath`.

## Helpers

| Helper | Signature |
|---|---|
| `getCitationLocation` | `(citation: ReviewCitation) => ReviewLocation \| undefined` |
| `getMetadataLocation` | `(metadata?, metadataPath?) => ReviewLocation \| undefined` |
| `getReviewFieldLocation` | `(field?, resolveLocation?) => ReviewLocation \| undefined` |
| `getReviewLocationKey` | `(location?) => string \| null` (stable `page:left:top:width:height`) |
| `findReviewField` | `(fields, fieldKey?) => ReviewField \| undefined` (supports dotted nested keys) |
| `boxesForPage` | `(fields, pageNumber, resolveLocation?) => CitationBox[]` (top-level fields only) |
| `formatCitationValue` | `(value: JsonValue) => string` (`null` shows as `NULL`) |
| `REVIEW_FIELDS` | demo bank-statement fields |

## Behavior in the block

- Focusing a field (hover, keyboard focus inside its card, or a programmatic `activeFieldKey`) draws the blue highlight on its page. Focus changes from the panel also smooth-scroll the PDF to center the box, including pages not yet rendered.
- Hovering a field card or array cell previews its box and scrolls instantly; leaving restores the active field's box.
- Every top-level field with a location gets a faint dashed clickable box on its page; clicking one focuses that field and scrolls its card into view.
- The split width (30–60% for the panel) persists in `localStorage` under `pdf-block-bounding-box-citations`. Below 900px container width the panes stack.

## Keyboard

- Split handle (`role="separator"`, "Resize review panel"): ArrowLeft widens the panel, ArrowRight narrows it (2% steps), Home sets the minimum, End the maximum.
- Form/JSON tabs: ArrowLeft/ArrowRight/Home/End move between tabs.
- Field cards are focusable groups; inside, standard inputs, plus `Undo <key>` and `Set <key> to null` buttons.
- Array grids: arrow keys move the selected cell; Enter, F2, or typing starts editing (Space toggles booleans); in the editor Enter commits and moves down, Tab/Shift+Tab commit and move sideways, Escape cancels. Object and array cells drill in.
- Citation boxes on the page are buttons (`aria-pressed` when active).

## Full example: mapping an extraction API response

```ts
// review-data.ts
import type {
	JsonObject, ReviewField, ReviewMetadataEntry
} from 'extend-ui-svelte/components/bounding-box-citations';

// Shape from your extraction backend.
export const apiResult = {
	value: {
		invoice_number: 'INV-20931',
		total: 1280.5,
		vendor: { name: 'Blue Ridge Freight', city: 'Asheville' },
		line_items: [
			{ description: 'Linehaul', amount: 1100 },
			{ description: 'Fuel surcharge', amount: 180.5 }
		]
	},
	metadata: {
		invoice_number: { citations: [{ page: 1, pageWidth: 612, pageHeight: 792,
			polygon: [{ x: 420, y: 72 }, { x: 560, y: 72 }, { x: 560, y: 90 }, { x: 420, y: 90 }] }] },
		total: { citations: [{ page: 1, pageWidth: 612, pageHeight: 792,
			polygon: [{ x: 440, y: 610 }, { x: 560, y: 610 }, { x: 560, y: 630 }, { x: 440, y: 630 }] }] },
		'vendor.name': { citations: [{ page: 1, pageWidth: 612, pageHeight: 792,
			polygon: [{ x: 48, y: 120 }, { x: 240, y: 120 }, { x: 240, y: 138 }, { x: 48, y: 138 }] }] },
		'line_items[0]': { citations: [{ page: 1, pageWidth: 612, pageHeight: 792,
			polygon: [{ x: 48, y: 400 }, { x: 564, y: 400 }, { x: 564, y: 418 }, { x: 48, y: 418 }] }] },
		'line_items[1]': { citations: [{ page: 1, pageWidth: 612, pageHeight: 792,
			polygon: [{ x: 48, y: 420 }, { x: 564, y: 420 }, { x: 564, y: 438 }, { x: 48, y: 438 }] }] }
	} satisfies Record<string, ReviewMetadataEntry>
};

const value = apiResult.value as JsonObject;

export const fields: ReviewField[] = [
	{ key: 'invoice_number', schema: { type: 'string', title: 'Invoice number' },
	  actual: value.invoice_number, expected: value.invoice_number },
	{ key: 'total', schema: { type: 'number', title: 'Total' },
	  actual: value.total, expected: value.total },
	{ key: 'vendor', schema: { type: 'object', title: 'Vendor', properties: {
		name: { type: 'string', title: 'Name' }, city: { type: 'string', title: 'City' } } },
	  actual: value.vendor, expected: value.vendor },
	{ key: 'line_items', schema: { type: 'array', title: 'Line items', items: { type: 'object', properties: {
		description: { type: 'string', title: 'Description' }, amount: { type: 'number', title: 'Amount' } } } },
	  actual: value.line_items, expected: value.line_items }
];
```

```svelte
<script lang="ts">
	import { BoundingBoxCitations } from 'extend-ui-svelte';
	import type { JsonObject } from 'extend-ui-svelte/components/bounding-box-citations';
	import { apiResult, fields } from './review-data';

	let values = $state<JsonObject>();
	let activeFieldKey = $state<string | null>(null);
</script>

<BoundingBoxCitations
	src="/documents/inv-20931.pdf"
	fileName="inv-20931"
	{fields}
	metadata={apiResult.metadata}
	bind:values
	bind:activeFieldKey
	height={760}
/>
<button type="button" onclick={() => fetch('/api/review', { method: 'POST', body: JSON.stringify(values) })}>
	Approve
</button>
```

The `vendor` card has no top-level citation, so it gets no faint box, but focusing its `name` property (key `vendor.name`) highlights the `vendor.name` citation.

## Gotchas

- `area` is percent 0–100. Passing pixels or 0–1 fractions draws boxes off-page or as dots.
- `page` is 1-based everywhere (`ReviewLocation`, `ReviewCitation`, PdfViewer's `pageNumber`). If your OCR uses 0-based pages, add 1.
- Polygons and `pageWidth`/`pageHeight` must share units. A citation without `pageWidth`, `pageHeight`, or polygon points resolves to nothing (no box, no error).
- If the reviewed PDF is a split of a larger source document, remap citation `page` from source pages to the split's local pages.
- Keep `fields` referentially stable. Recreating the array (for example inside a `$derived` that rebuilds on every change) resets the reviewer's edits in `values`.
- Setting `activeFieldKey` from the parent redraws the highlight but does not scroll the PDF; only focus changes from the panel or a page box scroll. To jump from external UI, focus the field card (`root.querySelector('[data-review-field="<key>"]').focus()`), which runs the block's own focus-and-scroll path. This relies on the `data-review-field` attribute in the source, not a documented API.
- Omitting `fields` shows the bank-statement demo. Always pass real fields.
- `values` holds top-level keys only; nested edits replace the whole object or array under that key.
- `boxesForPage` and the faint boxes cover top-level fields only; nested and array-row locations appear on focus or hover.
- Composing your own layout (`PdfViewer` + `HumanReviewPanel` + `HumanReviewHighlight` in `pageOverlay`) works for highlighting, but `PdfViewer` has no scroll-to-area API, so jump-to-box is lost. Children of `pageOverlay` need `pointer-events: auto` to be clickable.
- The array grid supports single-cell selection only (no range or drag selection).

## Differences from upstream (deliberate)

`theme` replaced by `isDark`/`onIsDarkChange` (no `HumanReviewTheme` type); `class` and `className` both accepted; DOM table grid instead of glide-data-grid; built-in line diff instead of `@pierre/diffs` (no word-level highlights); added `bind:values`, `bind:activeFieldKey`, `onActiveFieldChange`, `onFieldFocus`, `onLocationHover`, `fileName`, `height` on the block; `src` primary with `file` alias; faint clickable boxes for every located field; scroll-to-area computed from rendered pages; split stacks below 900px. The parity suite records no unrecorded props.
