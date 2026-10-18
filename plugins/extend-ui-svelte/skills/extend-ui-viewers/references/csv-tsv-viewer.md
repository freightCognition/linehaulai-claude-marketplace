# CsvTsvViewer

Source: `src/lib/components/csv-tsv-viewer/` (`CsvTsvViewer.svelte`, `parse.ts`). Parsing uses `papaparse@^5.7`, loaded with a dynamic import.

```ts
import { CsvTsvViewer, CsvViewer, parseDelimitedText, type CsvTsvViewerProps, type ParsedTable } from 'extend-ui-svelte';
import { CsvTsvViewer } from 'extend-ui-svelte/components/csv-tsv-viewer';
// registry copy-in: '$lib/components/csv-tsv-viewer/index.js'
```

The root also exports `CsvTsvViewerDefault`, which is the same component.

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `data` | `string` | `''` | Raw CSV or TSV **text**, not a URL. Fetch the file or call `file.text()` first. |
| `search` | `boolean` | `false` | Shows the search button and its find popover. |
| `delimiter` | `string` | `''` | An explicit delimiter, such as `'\t'`. An empty string means papaparse auto-detects. |
| `isDark` | `boolean` | `false` | Dark theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Accepted for contract parity. Never called. |
| `rowHeight` | `number` | `34` | Fixed row height in px, used for windowing. |
| `height` | `number` | `560` | Viewport height in px. |
| `overscan` | `number` | `5` | Extra rows rendered above and below the window. |
| `class` / `className` | `string` | `''` | Both are merged. |

There are no callbacks.

## Parsing rules (`parseDelimitedText(text, delimiter = ''): Promise<ParsedTable>`)

`ParsedTable` is `{ headers: string[]; rows: string[][]; error: string | null }`.

- The first row is the header (`header: true`). Empty lines are skipped greedily.
- A blank header becomes `Column N`. Ragged rows with extra cells add `Extra N` columns, and shorter rows are padded with `''`.
- `error` is set only when nothing parsed. In that case the viewer shows the error instead of a table.
- The function is async and usable on its own, for example to preview headers before mounting the viewer.

## Search and keyboard

- The search button (labeled "Search CSV") toggles a popover (`role="dialog"`). The input is focused when it opens.
- Typing is debounced by 300ms, and matching is a case-insensitive substring match over every cell.
- Enter goes to the next match and Shift+Enter to the previous one. Previous and Next buttons do the same.
- The label shows `n / total` and the address of the active match (`Header!B12`). The active cell is scrolled to the vertical center and highlighted.
- Escape closes the popover and returns focus to the button. A click outside closes it, and so does changing `data`.
- The button is disabled while parsing, on a parse error, or when there are no rows.

## Full example: load a remote file

```svelte
<script lang="ts">
  import { CsvTsvViewer } from 'extend-ui-svelte/components/csv-tsv-viewer';

  let { url }: { url: string } = $props();
  let text = $state('');
  let failed = $state('');

  $effect(() => {
    const u = url;
    let cancelled = false;
    fetch(u)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((t) => { if (!cancelled) text = t; })
      .catch((e) => { if (!cancelled) failed = String(e); });
    return () => { cancelled = true; };
  });
</script>

{#if failed}
  <p role="alert">{failed}</p>
{:else}
  <CsvTsvViewer data={text} delimiter={url.endsWith('.tsv') ? '\t' : ''} search height={600} />
{/if}
```

## Gotchas

- **The toolbar always renders**, with a row count and the optional search button. There is no `showToolbar` prop.
- **Large files.** Rows are windowed in a native `<table>` using top and bottom padding rows. Parsing is one papaparse pass over the whole string, and search is one synchronous scan, so files with hundreds of thousands of rows can stall typing in the search box.
- **Pass text, not a URL.** `data="/file.csv"` renders a one-column table whose header is the path.
- **SSR.** Parsing runs in `$effect`, so the server renders an empty table with "0 rows".

## Differences from upstream React `CsvViewer`

- The grid is a windowed `<table>` instead of glide-data-grid.
- Not ported: zoom, upload, download, cell selection, and column resize.
- Port-only props: `delimiter`, `isDark`, `onIsDarkChange`, `rowHeight`, `height`, `overscan`.
- Dark mode is parent-controlled. Upstream reads `.dark` from the document.
