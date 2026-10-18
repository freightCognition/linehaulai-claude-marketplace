# Engines, the PDF worker, and SSR

## How components load engines

Every engine touches `window`, canvas, `DOMParser`, or workers. The library keeps them off the server two ways:

1. Engine modules load their third-party library lazily. `engines/pdf/pdf-engine.ts` calls `import('pdfjs-dist')` on first `load()`, `engines/xlsx/xlsx.ts` calls `import('xlsx')`, `engines/docx/index.ts` calls `import('docx-preview')` inside `renderDocx`, and `engines/pptx/pptx.ts` calls `import('pptx-browser')` inside `loadDeck`. Importing the engine modules themselves is DOM-free.
2. Components call the engines from `onMount` or `$effect`, which never run during SSR (for example `PdfViewer` does `await import('../../engines/pdf/index.js')`).

So in SvelteKit you do **not** need `export const ssr = false` or `{#if browser}` around a viewer. The server renders the shell (toolbar, empty viewport); the client loads the document.

Use `ssr = false` only when your own page code touches browser APIs at module scope.

## Calling engines yourself (copy-in only)

Engines are not exported by the npm package. With the copied `engines` item:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import type { WorkBook } from '$lib/extend-ui/engines/xlsx/index.js';

	let workbook = $state.raw<WorkBook | null>(null);
	let sheetNames = $state.raw<string[]>([]);

	onMount(async () => {
		const { loadWorkbookFromUrl, listSheetNames } = await import(
			'$lib/extend-ui/engines/xlsx/index.js'
		);
		workbook = await loadWorkbookFromUrl('/files/report.xlsx');
		sheetNames = listSheetNames(workbook);
	});
</script>
```

Type-only imports (`import type`) are erased and are safe at module scope.

If code must run outside `onMount`, guard it with `browser` from `$app/environment`:

```ts
import { browser } from '$app/environment';
if (browser) {
	const { createPdfEngine } = await import('$lib/extend-ui/engines/pdf/index.js');
}
```

Never import engines from `+page.server.ts`, `+layout.server.ts`, `+server.ts`, or hooks.

## Engine APIs (from source)

### PDF: `engines/pdf/index.ts`

Exports `createPdfEngine`, `isPdfLoadSuperseded`, `setPdfWorkerSrc`, plus types `PdfEngine`, `PdfPageChangeHandler`, `PdfPageSize`, `PdfRenderOptions`, `PdfSource`.

- `PdfSource = string | URL | ArrayBuffer | Uint8Array`
- `createPdfEngine(): PdfEngine` with:
  - `load(source): Promise<number>` resolves with the page count. Last call wins: a superseded load rejects with an error where `isPdfLoadSuperseded(error)` is true. Ignore those.
  - `getPageSizes(): Promise<PdfPageSize[]>` gives sizes at scale 1 with each page's rotation.
  - `renderPage(pageNumber, canvas, { scale?, rotation? }): Promise<PdfPageSize>` uses 1-based pages.
  - `pageCount`, `currentPage` (0 when unloaded), `setCurrentPage(page)`, `onPageChange(handler)` returns an unsubscribe function.
  - `destroy(): Promise<void>`. Call it in cleanup.

```ts
onMount(() => {
	let engine: import('$lib/extend-ui/engines/pdf/index.js').PdfEngine | undefined;
	(async () => {
		const { createPdfEngine, isPdfLoadSuperseded } = await import('$lib/extend-ui/engines/pdf/index.js');
		engine = createPdfEngine();
		try {
			const pages = await engine.load('/files/a.pdf');
			await engine.renderPage(1, canvas, { scale: 1.5 });
		} catch (error) {
			if (!isPdfLoadSuperseded(error)) throw error;
		}
	})();
	return () => void engine?.destroy();
});
```

### The PDF.js worker

`pdf-engine.ts` does `import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'` and assigns it to `GlobalWorkerOptions.workerSrc` before any `getDocument`. Consequences:

- No setup is needed in a Vite app. The worker file is emitted as an asset and always matches the installed `pdfjs-dist` version.
- The host bundler must support Vite's `?url` suffix. SvelteKit does. With the npm package, the `?url` import lives in `node_modules/extend-ui-svelte/dist/engines/pdf/pdf-engine.js`; vite-plugin-svelte keeps Svelte libraries out of dependency pre-bundling, so Vite processes it normally.
- To serve the worker from a CDN or a custom path, call `setPdfWorkerSrc(url)` once on the client before the first viewer mounts (it also patches an already-loaded PDF.js). The URL must point at the worker build for the same `pdfjs-dist` version, otherwise PDF.js throws a version mismatch. This function is only available with the copied `engines` item.
- `worker-url.d.ts` declares the `?url` module so consumers without `vite/client` types still type-check. Copy it along with the engine.

### DOCX: `engines/docx/index.ts`

- `renderDocx(source: DocxSource, container: HTMLElement, options?: DocxRenderOptions): Promise<DocxRenderResult>`; `DocxSource = Blob | ArrayBuffer | Uint8Array | string` (a string is a URL to fetch).
- `DocxRenderOptions`: `showThumbnails?` (default false), `className?` (default `'docx'`), `breakPages?` (default true).
- Rejects with `DocxRenderError` without a DOM and with `DocxRenderCancelledError` when a newer render into the same container supersedes it.
- Output is sanitized: scripts, iframes, objects and embeds are dropped, and only http(s), mailto, tel, and `#anchor` links are kept (`isSafeDocxLinkTarget`, `isSafeDocxImageSource`, `sanitizeDocxNode`). `clearDocx(container)` empties it.

### XLSX: `engines/xlsx/index.ts`

- `loadWorkbookFromBytes(data: ArrayBuffer | Uint8Array): Promise<WorkBook>` rejects on empty input. `loadWorkbookFromUrl(url): Promise<WorkBook>`.
- `listSheetNames(workbook): string[]` (sync).
- `sheetToRows<T>(workbook, sheetName, options?)` uses header-keyed rows via `sheet_to_json` (blanks default to `''`).
- `sheetToGrid(workbook, sheetName): Promise<XlsxSheetGrid>` returns `{ values: unknown[][]; formulas: Record<'row:col', string> }` anchored at A1. Error cells come back as `XlsxCellError`.
- `getSheetRowCount`, `XLSX_ERROR_CODES`, `XlsxCellError`, and the `WorkBook` type re-exported from `xlsx`.

### PPTX: `engines/pptx/index.ts`

- `loadDeck(data: ArrayBuffer | Uint8Array, onProgress?): Promise<PptxDeck>`
- `PptxDeck`: `slideCount`, `renderSlide(index /* 0-based */, canvas, width = DEFAULT_RENDER_WIDTH /* 1280 */)`, `destroy()`.
- Engine is `pptx-browser` (zero dependencies; uses `DecompressionStream`, `DOMParser`, and Canvas 2D). `pptxviewjs` was rejected because its bundle hard-imports `chart.js`.

## `$state.raw` for large documents

Svelte 5 `$state` deep-proxies objects. A SheetJS `WorkBook`, a parsed CSV table, page-size arrays, or a `Uint8Array` gain nothing from fine-grained reactivity and get slow when proxied. The library itself uses `$state.raw` for these (for example `CsvTsvViewer` keeps `parsed` and search `results` raw, and `VirtualList` keeps its measurement map raw).

```ts
let workbook = $state.raw<WorkBook | null>(null);
let bytes = $state.raw<Uint8Array | null>(null);
// Update by reassignment, never by mutation:
workbook = await loadWorkbookFromBytes(next);
```

Pass `data` (bytes) to `XlsxViewer` and `XlsxEditor` from a raw state value too.

## Passing files from inputs

Viewers that take `src?: string` want a URL. For a user-selected `File`, use `URL.createObjectURL(file)` and revoke it in cleanup:

```ts
let src = $state<string | undefined>();
$effect(() => {
	if (!file) return;
	const url = URL.createObjectURL(file);
	src = url;
	return () => URL.revokeObjectURL(url);
});
```

`PdfEditor` `src` also accepts `ArrayBuffer | Uint8Array | Blob`. `XlsxViewer` and `XlsxEditor` accept `data?: ArrayBuffer | Uint8Array`.
