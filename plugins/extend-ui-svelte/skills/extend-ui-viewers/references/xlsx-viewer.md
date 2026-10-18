# XlsxViewer

Source: `src/lib/components/xlsx-viewer/` (`XlsxViewer.svelte`, `WorkbookSheetTabs.svelte`, `grid-navigation.ts`). Parsing uses the xlsx engine (`src/lib/engines/xlsx`), which wraps SheetJS `xlsx@0.20.3` from the SheetJS CDN tarball.

```ts
import { XlsxViewer, XlsxViewerPreview, WorkbookSheetTabs } from 'extend-ui-svelte';
import { XlsxViewer, type XlsxViewerProps } from 'extend-ui-svelte/components/xlsx-viewer';
// registry copy-in: '$lib/components/xlsx-viewer/index.js'
```

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `isDark` | `boolean` | `false` | **Required** by the type. Dark theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | **Required.** Called by the toolbar's Dark/Light switch. |
| `src` | `string` | `undefined` | The workbook URL, loaded with `fetch` on the client. |
| `data` | `ArrayBuffer \| Uint8Array` | `undefined` | The workbook bytes. Takes precedence over `src`. Use this for a `File`: `await file.arrayBuffer()`. |
| `fileName` | `string` | `undefined` | The name shown in the toolbar. Falls back to the basename of `src`, then `workbook.xlsx`. |
| `showToolbar` | `boolean` | `true` | Toolbar showing the name, row count, and theme switch. |
| `rowHeight` | `number` | `34` | Fixed row height in px. The virtualization math depends on it. |
| `height` | `number` | `480` | Viewport height in px. |
| `overscan` | `number` | `5` | Extra rows rendered above and below the window. |
| `class` / `className` | `string` | `''` | Both are merged. |

There are no callbacks besides `onIsDarkChange`. The active sheet and the selected cell are internal state.

## Rendering

- Column letters (A, B, …, AA) and row numbers start from A1. Row 1 is treated as data, not a header, and blank rows are kept.
- Each column is 150px wide and the row-number column is 48px. The grid scrolls horizontally.
- Booleans display as `TRUE` and `FALSE`, and error cells display their code. Cell formatting is not rendered.
- `WorkbookSheetTabs` renders below the grid once the workbook is ready. It renders nothing for a single-sheet workbook.

## Keyboard (grid)

The grid (`role="grid"`, `aria-readonly`) is a single Tab stop and uses `aria-activedescendant`. Clicking a cell selects it. Key bindings, from `grid-navigation.ts`:

- Arrow keys move one cell.
- Ctrl or Cmd plus an arrow jumps to the edge of the used range.
- Home and End go to the first and last used column.
- PageUp and PageDown move by one viewport of rows. Alt+PageUp and Alt+PageDown move by one viewport of columns.
- Tab and Shift+Tab move right and left. Enter and Shift+Enter move down and up.
- With no cell selected, keys start from A1.
- Shift+arrow moves the selection; it does not extend a range. There is no copy.

## Keyboard (sheet tabs)

- ArrowLeft and ArrowRight move focus and wrap at the ends. Home and End jump to the first and last tab.
- Enter or Space activates the focused tab.
- Only the focused tab is in the tab order.

## `WorkbookSheetTabs` (standalone)

| Prop | Type | Description |
|---|---|---|
| `sheets` | `string[]` | Sheet names in workbook order. |
| `activeSheetIndex` | `number` | The zero-based active tab. |
| `onActiveSheetIndexChange` | `(index: number) => void` | Called when the user picks a tab. |

Colors come from the host's `--xlsx-*` custom properties.

## Full example: local file or URL

```svelte
<script lang="ts">
  import { XlsxViewer } from 'extend-ui-svelte/components/xlsx-viewer';

  let isDark = $state(false);
  let bytes = $state<ArrayBuffer | undefined>();
  let name = $state('rates.xlsx');

  async function pick(e: Event & { currentTarget: HTMLInputElement }) {
    const file = e.currentTarget.files?.[0];
    if (!file) return;
    name = file.name;
    bytes = await file.arrayBuffer();
  }
</script>

<input type="file" accept=".xlsx,.xls,.ods" onchange={pick} />
<XlsxViewer
  src="/files/rates.xlsx"
  data={bytes}
  fileName={name}
  height={640}
  {isDark}
  onIsDarkChange={(v) => (isDark = v)}
/>
```

## Gotchas

- **Workbook caching.** The parsed workbook is cached by source identity: the `data` object reference, or the `src` string. Pass a new `ArrayBuffer` to force a reload. Mutating the same buffer in place does not trigger one.
- **Large sheets.** Rows are virtualized, but columns are not: every column of each visible row renders. Very wide sheets cost proportionally more. The whole sheet is converted to a values grid when its tab opens.
- **Errors** render in-place (`role="alert"`) with the SheetJS or fetch message.
- **SSR.** The engine loads inside `$effect`, so the server renders the empty or loading state.

## Differences from upstream React `XlsxViewerPreview`

- Not ported: cell formatting (fonts, fills, borders, number formats, merged cells), frozen panes, column resize, zoom, search, sheet thumbnails, range selection, and copy.
- Also not ported: the upload and download menu. The props `showDownload`, `showUpload`, and `toolbarActions` do not exist here.
- Port-only props: `data`, `rowHeight`, `height`, `overscan`.
- The theme switch is a toolbar button, not an item in a menu.
- `WorkbookSheetTabs` takes props instead of a react-xlsx context.
- Not exported: `renderXlsxScroller`, `WorkbookTableHeaderMenu`, `XlsxWorkbookSurface`.
