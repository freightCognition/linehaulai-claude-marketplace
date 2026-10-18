# PdfViewer

Source: `src/lib/components/pdf-viewer/` (`PdfViewer.svelte`, `PdfPage.svelte`, `types.ts`, `zoom.ts`). It renders through the shared PDF.js engine (`src/lib/engines/pdf`, which uses `pdfjs-dist@^6`). Downloading rotated pages uses `pdf-lib`.

```ts
import { PdfViewer, PDFViewer, type PdfViewerProps } from 'extend-ui-svelte';
import {
  PdfViewer,
  type PdfViewerPageOverlayProps,
  type PdfViewerZoomLevel,
  ZOOM_OPTIONS, MIN_ZOOM, MAX_ZOOM
} from 'extend-ui-svelte/components/pdf-viewer';
// registry copy-in: '$lib/components/pdf-viewer/index.js'
```

## Props

No prop is `$bindable`. Every prop is one-way.

| Prop | Type | Default | Description |
|---|---|---|---|
| `src` | `string` | `undefined` | The PDF URL, which can be an object URL or a data URL. When empty, the viewer shows the upload prompt. It must be a string: `ArrayBuffer` and `File` are not accepted at the component level. |
| `fileName` | `string` | `undefined` | The download name. `.pdf` is appended if missing. Falls back to the basename of `src`. |
| `defaultZoom` | `PdfViewerZoomLevel` (`number \| 'fit-page' \| 'fit-width' \| 'automatic'`) | `1` | The initial zoom. Re-applied each time a document loads; uncontrolled after that. |
| `showToolbar` | `boolean` | `true` | Renders the toolbar. |
| `showDownload` | `boolean` | `true` | Download button. |
| `showRotateControls` | `boolean` | `true` | Rotate buttons. These rotate the **active page only**. |
| `showUpload` | `boolean` | `true` | Upload control (accepts `application/pdf,.pdf`). |
| `pageClassName` | `(pageNumber: number) => string \| undefined` | `undefined` | Extra class for each page wrapper. Scoped CSS needs `:global(...)` to style it. |
| `pageOverlay` | `Snippet<[PdfViewerPageOverlayProps]>` | `undefined` | Rendered on top of each **visible** page. |
| `toolbarActions` | `Snippet` | `undefined` | Extra toolbar content, placed before Download and Upload. |
| `onActivePageChange` | `(pageNumber: number) => void` | `undefined` | Called when the topmost or most visible page changes. |
| `onDocumentLoadSuccess` | `(numPages: number) => void` | `undefined` | Called after load, with the page count. |
| `onPdfUpload` | `(file: File) => void` | `undefined` | Called with the file chosen through the upload control. The viewer displays it until `src` changes. |
| `isDark` | `boolean` | `false` | Dark theme. Adds the `.dark` class and `data-dark`. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Accepted for the shared contract. Never called, because the viewer has no theme switch. |
| `height` | `number` | `600` | Viewport height in px. Drives windowing. |
| `pageWidth` | `number` | `612` | Fallback page width at zoom 1, used until real sizes load. |
| `pageHeight` | `number` | `792` | Fallback page height at zoom 1. |
| `pageGap` | `number` | `24` | Gap in px around and between pages. |
| `overscan` | `number` | `DEFAULT_OVERSCAN` (3) | Extra pages rendered above and below the window. |
| `class` / `className` | `string` | `''` | Both are merged onto the root. |

## Overlay snippet props (`PdfViewerPageOverlayProps`)

```ts
interface PdfViewerPageOverlayProps {
  pageNumber: number;
  pageWidth: number;   // unrotated width at scale 1
  pageHeight: number;  // unrotated height at scale 1
  scale: number;       // current zoom
  rotation: number;    // degrees; the overlay layer rotates with the page
}
```

The overlay box is `pageWidth * scale` by `pageHeight * scale` and is rotated with the page. Place children in PDF-point space multiplied by `scale`, and the overlay stays aligned through zoom and rotation. The layer has `pointer-events: none`, so set `pointer-events: auto` on interactive children.

## Exported helpers (from `zoom.ts`)

`DEFAULT_ZOOM` (1), `ZOOM_OPTIONS` (`[0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2]`), `MIN_ZOOM`, `MAX_ZOOM`, `ZOOM_MODES`, `isZoomMode`, `clampZoom`, `resolveZoom`, `computeFitZoom`, `zoomStepIn`, `zoomStepOut`, `zoomSelectOptions`, `zoomSelectValue`, `formatZoomPercent`, `normalizeRotation`, `rotateClockwise`, `rotateCounterClockwise`, `rotatedPageSize`, `computePageLayout`, `pageWindow`, `pageAtOffset`, `ensurePdfExtension`, `getPdfDownloadFileName`, `getRotatedPdfDownloadFileName`.

Types: `PdfViewerZoomLevel`, `PdfViewerZoomMode`, `PdfLayoutSize`, `PdfPageLayout`, `ZoomViewport`, plus the uppercase aliases `PDFViewerProps`, `PDFViewerPageOverlayProps`, and `PDFViewerZoomLevel`.

## Keyboard and accessibility

- The toolbar has `role="toolbar"`. The scroll viewport (`role="group"`, label "PDF pages") has `tabindex="0"`, so arrow keys, PageUp/PageDown, and Space scroll it natively.
- There are no custom key bindings.
- Zoom uses a native `<select>` labeled "Zoom level".

## Full example: highlight extracted fields

```svelte
<script lang="ts">
  import { PdfViewer, type PdfViewerPageOverlayProps } from 'extend-ui-svelte/components/pdf-viewer';

  type Box = { page: number; x: number; y: number; w: number; h: number; label: string };
  // Coordinates in PDF points (scale 1, top-left origin).
  let { src, boxes = [] }: { src: string; boxes?: Box[] } = $props();

  let page = $state(1);
  let total = $state(0);
  let isDark = $state(false);
</script>

<p>Page {page} / {total || '–'}</p>

<PdfViewer
  {src}
  fileName="statement"
  defaultZoom="fit-width"
  height={720}
  {isDark}
  onActivePageChange={(p) => (page = p)}
  onDocumentLoadSuccess={(n) => (total = n)}
>
  {#snippet pageOverlay(o: PdfViewerPageOverlayProps)}
    {#each boxes.filter((b) => b.page === o.pageNumber) as b (b.label)}
      <button
        type="button"
        class="hl"
        title={b.label}
        style:left="{b.x * o.scale}px"
        style:top="{b.y * o.scale}px"
        style:width="{b.w * o.scale}px"
        style:height="{b.h * o.scale}px"
        onclick={() => console.log(b.label)}
      ></button>
    {/each}
  {/snippet}
  {#snippet toolbarActions()}
    <button type="button" onclick={() => (isDark = !isDark)}>Theme</button>
  {/snippet}
</PdfViewer>

<style>
  .hl {
    position: absolute;
    pointer-events: auto; /* overlay layer is pointer-events: none */
    background: rgb(250 204 21 / 0.3);
    border: 1px solid rgb(202 138 4);
    padding: 0;
  }
</style>
```

To show a local `File`:

```svelte
<script lang="ts">
  let file = $state<File | null>(null);
  const url = $derived(file ? URL.createObjectURL(file) : undefined);
  $effect(() => { const u = url; return () => { if (u) URL.revokeObjectURL(u); }; });
</script>
<input type="file" accept="application/pdf" onchange={(e) => (file = e.currentTarget.files?.[0] ?? null)} />
<PdfViewer src={url} />
```

## Gotchas

- **Worker.** The engine imports `pdfjs-dist/build/pdf.worker.mjs?url`, a Vite `?url` import, so the worker version always matches the installed pdfjs-dist. This works out of the box with SvelteKit and Vite. Non-Vite bundlers must handle `?url` imports. `setPdfWorkerSrc(url)` lives in `engines/pdf`, which the package `exports` map does not expose: only registry copy-in users can call it, from `$lib/engines/pdf/index.js`.
- **Virtualization.** Only pages inside the scroll window plus `overscan` are mounted, each as a canvas. Large PDFs stay cheap. The overlay snippet renders only for mounted pages, so do not rely on it for off-screen pages.
- **Errors.** Load failures show the fixed message "Unable to load the PDF preview.", never the raw PDF.js error. Engine import failures show "Unable to load the PDF engine." There is no error callback.
- **CORS.** A cross-origin `src` must send CORS headers, because PDF.js fetches it and Download uses `fetch(src)`.
- **Rotation** applies only to the active page. Download then saves a copy rewritten by pdf-lib, named `*-rotated.pdf`.
- **SSR.** `onMount` loads the engine, so the server renders the toolbar and the loading or empty state.

## Differences from upstream React `PDFViewer`

- Not ported: text search, text selection, the thumbnail sidebar, tiling, `resolveScrollAreaViewport`, and the imperative ref handle (`PDFViewerHandle`).
- Upstream's `onPagePointerDown`, `onPagePointerMove`, `onPagePointerUp`, and `onPagePointerCancel` are missing and unrecorded. They appear in `KNOWN_UNRECORDED_PROPS` in `src/lib/parity/port-parity.test.ts`.
- `renderPageOverlay` becomes the `pageOverlay` snippet.
- Download and Upload are buttons, not a menu.
- Previous and Next buttons are added.
- Port-only props: `height`, `pageWidth`, `pageHeight`, `pageGap`, `overscan`.
- The engine is PDF.js instead of the `@embedpdf` stack.
