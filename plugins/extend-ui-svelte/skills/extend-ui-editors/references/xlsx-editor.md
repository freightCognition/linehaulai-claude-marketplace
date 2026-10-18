# XlsxEditor reference

Source: `src/lib/components/xlsx-editor/XlsxEditor.svelte`, `formulas.ts`, `workbook-export.ts`, `index.ts`.

```ts
import { XlsxEditor, XlsxEditorPreview } from 'extend-ui-svelte';
import {
	type XlsxEditorProps, type XlsxCellChange, type XlsxCellStyle, type XlsxCellAlign,
	type CellValue, type CellCoord, type CellGetter, type EditableSheet,
	columnIndexToLetter, columnLetterToIndex, parseCellRef, expandRange, evaluateCell,
	sheetsToXlsxBytes, downloadXlsxBytes
} from 'extend-ui-svelte/components/xlsx-editor';
// Registry copy-in: same names from '$lib/components/xlsx-editor/index.js'
```

The workbook loads through the shared XLSX engine (SheetJS) on the client. Every sheet is converted to an A1-anchored grid, keeping blank rows and columns so addresses match the file.

## Props

No props are `$bindable`.

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `isDark` | `boolean` | `false` | **yes (TS)** | Parent-controlled theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | **yes (TS)** | Called by the toolbar's dark/light switch. |
| `src` | `string` | — | | Workbook URL, fetched on the client. |
| `data` | `ArrayBuffer \| Uint8Array` | — | | Workbook bytes. Wins over `src`. (Port-only.) |
| `fileName` | `string` | derived | | Toolbar name. Export adds `.xlsx`. Fallbacks: the `src` basename, then `workbook.xlsx`. |
| `showToolbar` | `boolean` | `true` | | Name, row count, Export, theme switch, formula bar, and style controls. **With `false`, the formula bar, style controls, and Export button are all hidden.** |
| `rowHeight` | `number` | `34` | | Fixed row height in px, used for virtualization. |
| `height` | `number` | `480` | | Grid viewport height in px. |
| `overscan` | `number` | `5` | | Extra rows rendered beyond the viewport. |
| `onCellChange` | `(change: XlsxCellChange) => void` | — | | Called after each committed edit. |
| `onExport` | `(bytes: Uint8Array, fileName: string) => void` | — | | Called after the Export download. |
| `class` / `className` | `string` | `''` | | Merged together. |

## Types

```ts
type CellValue = string | number | boolean | null | XlsxCellError;
interface XlsxCellChange { sheet: string; row: number; col: number; value: CellValue } // zero-based
type XlsxCellAlign = 'left' | 'center' | 'right';
interface XlsxCellStyle { bold?: boolean; align?: XlsxCellAlign; fill?: string }
interface EditableSheet { name: string; grid: CellValue[][]; formulas?: Record<string /* "row:col" */, string /* no "=" */> }
```

`onCellChange` value rules:
- Text beginning with `=` becomes a formula, and `value` is the trimmed text with `=`, for example `"=SUM(A1:A3)"`.
- Numeric text is converted to a `number`. Blank input becomes `null`. Anything else stays a string.
- Delete or Backspace on a cell reports `value: null`.
- Committing unchanged text reports nothing.

## Helpers

- `sheetsToXlsxBytes(sheets: EditableSheet[]): Promise<Uint8Array>` writes each cell at its own address. Formula cells are written as `{ f }` together with their value. It throws on an empty array.
- `downloadXlsxBytes(bytes, fileName): boolean` returns `false` instead of throwing when the browser cannot download.
- `evaluateCell(raw, get)`, `parseCellRef('B3')` (returns `{ row: 2, col: 1 }`, zero-based), `expandRange('A1:B2')`, `columnIndexToLetter(0)` (returns `'A'`), `columnLetterToIndex('AA')`.

Local formula engine: SUM, AVERAGE, MIN, MAX, COUNT, PRODUCT, TRUE/FALSE, and arithmetic over same-sheet A1 references. A formula keeps the value saved in the file until it or one of its inputs is edited. After that, cross-sheet references, other functions, and comparisons keep the saved value and do not recalculate.

## Keyboard (the grid is a single Tab stop)

- Arrow keys, Ctrl/Cmd+arrows, Home, End, PageUp, PageDown, Tab and Shift+Tab, and Enter and Shift+Enter move the active cell.
- Typing a printable key starts an edit with that character. F2 edits the current text. Delete or Backspace clears the cell.
- In the cell editor, Enter commits and stays on the cell, Escape cancels, and arrow keys commit and move.
- In the formula bar, Enter commits (by blurring the field).
- Not ported: range selection (Shift+arrows move instead of extending), copy/paste, undo/redo, and the column sort menu.

## Snippets

None. Sheet tabs come from xlsx-viewer's `WorkbookSheetTabs` and appear automatically.

## Example

See `../examples/edit-spreadsheet-save-to-api.svelte`.

To save without the forced download, rebuild the sheets yourself from `onCellChange` events applied to your own copy of the workbook data, then call `sheetsToXlsxBytes(sheets)`. Neither the component nor its exports give access to the internal grids.

## Gotchas

- Export always downloads first and then calls `onExport`. It cannot be suppressed.
- **Styles are not exported.** Bold, alignment, and fill are editor-only state (the community SheetJS writer drops them). Number formats, merges, column widths, and file formatting are not read or written either.
- A new `src` or `data` reference wipes all edits, styles, and the selection. Keep the bytes in stable state, for example `$state.raw`.
- Every sheet parses up front, and upstream's read-only mode for files over 5 MB is not ported. Very large workbooks cost memory and load time.
- Not ported: italic, underline, strikethrough, fonts, text color, borders, number formats, merges, wrap, vertical align, undo/redo, add/remove sheet, frozen panes, column resize, zoom, upload menu. The prop list matches upstream exactly; the parity ledger records no missing props.
