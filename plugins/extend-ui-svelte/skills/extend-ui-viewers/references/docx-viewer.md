# DocxViewer

Source: `src/lib/components/docx-viewer/DocxViewer.svelte`. Rendering uses the docx engine (`src/lib/engines/docx`), which wraps `docx-preview` and `jszip`.

```ts
import { DocxViewer, DocxViewerPreview } from 'extend-ui-svelte';
import {
  DocxViewer,
  type DocxViewerProps,
  type DocxViewerZoomLevel,
  DOCX_MIME_TYPE, DOCX_UPLOAD_ACCEPT, ZOOM_OPTIONS
} from 'extend-ui-svelte/components/docx-viewer';
// registry copy-in: '$lib/components/docx-viewer/index.js'
```

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `isDark` | `boolean` | `false` | **Required** by the type. Dark theme, applied as CSS overrides on the docx-preview output. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | **Required.** Called by the toolbar's Dark/Light switch. |
| `src` | `string` | `undefined` | The DOCX URL, which can be an object URL. When empty, the viewer shows the "Upload Word document" prompt. |
| `fileName` | `string` | `undefined` | Display and download name. Falls back to the basename of `src`. `.docx` is appended on download. |
| `showToolbar` | `boolean` | `true` | Toolbar containing thumbnails, paging, zoom, and actions. |
| `showDownload` | `boolean` | `true` | Download button. |
| `showUpload` | `boolean` | `true` | Upload button. The hidden file input stays mounted either way, because the empty-state button uses it. |
| `defaultZoom` | `DocxViewerZoomLevel` (`number \| 'fit-page' \| 'fit-width' \| 'automatic'`) | `50` | The initial zoom **in percent**. `'automatic'` fits the width but never goes above 100%. It resets on each new document. |
| `toolbarActions` | `Snippet` | `undefined` | Extra toolbar content, placed before Upload and Download. |
| `class` / `className` | `string` | `''` | Both are merged. |

There are no load, error, or page-change callbacks.

## Exported helpers

- Constants: `ZOOM_OPTIONS` (`[50, 75, 100, 125, 150, 175, 200]`), `DEFAULT_ZOOM` (50), `ZOOM_MODE_LABELS`, `THUMBNAIL_ITEM_HEIGHT` (72), `DOCX_MIME_TYPE`, `DOCX_UPLOAD_ACCEPT`.
- Functions: `resolveZoomLevel(level, metrics)`, `stepZoom(current, direction)`, `formatDocumentName(fileName, url)`, `ensureDocxExtension(name)`.
- Types: `DocxViewerPage` (`{ pageNumber; excerpt }`), `DocxViewerZoomLevel`, `DocxZoomMetrics`, `DocxViewerProps`.

## Toolbar and keyboard

- "Thumbnails" toggles the built-in sidebar. It is a virtualized `listbox` of page numbers with 80-character text excerpts, not rendered images. The listbox takes focus and uses `aria-activedescendant`. ArrowUp and ArrowDown step between pages, Home and End jump to the ends, and clicking a row jumps to that page.
- Previous and Next buttons sit beside a clickable page number. Clicking the number turns it into an input: typing a whole number jumps (clamped to the page range), and Enter or Escape commits and blurs.
- The zoom controls are minus and plus buttons around a `<select>` of fit modes and percentages.
- The document viewport (`role="group"`, label "Document pages") is focusable for native scrolling.

## Full example

```svelte
<script lang="ts">
  import { DocxViewer } from 'extend-ui-svelte/components/docx-viewer';

  let { src }: { src: string } = $props();
  let isDark = $state(false);
</script>

<DocxViewer
  {src}
  fileName="Master Services Agreement"
  defaultZoom="automatic"
  {isDark}
  onIsDarkChange={(v) => (isDark = v)}
>
  {#snippet toolbarActions()}
    <a href={src} target="_blank" rel="noopener">Open original</a>
  {/snippet}
</DocxViewer>
```

## Gotchas

- **Fixed height.** There is no `height` prop. The root `.docx-viewer` is 640px tall, toolbar included, through scoped CSS. To change it, pass a class and use a global selector that outranks the scoped rule, for example `class="tall"` with `:global(div.docx-viewer.tall) { height: 80vh; }`. The scoped rule has specificity (0,2,0), so `div.docx-viewer.tall` at (0,2,1) wins.
- **No virtualization of pages.** docx-preview builds the DOM for every page. Off-screen pages skip layout and paint through `content-visibility: auto`. Very long documents still cost memory and parse time up front.
- **Sanitized output.** The engine keeps only `http(s)`, `mailto`, `tel`, and `#anchor` links, and strips scripts, frames, objects, embeds, and `on*` attributes.
- **Not supported:** comments, tracked changes, outline anchors, and canvas thumbnails. Legacy `.doc` files are accepted by the upload input but fail to render.
- **Errors** appear in-place (`data-testid="docx-error"`, `role="alert"`) with the engine message.
- **SSR.** The engine is imported in `onMount`, so the server renders the empty prompt (when `src` is empty) or the loading state.

## Differences from upstream React `DocxViewerPreview`

- The renderer is docx-preview instead of `@extend-ai/react-docx`.
- The thumbnail sidebar is text excerpts, virtualized with `VirtualList`, and always inline. It never collapses to an overlay.
- Previous and Next buttons are added.
- Zoom is CSS zoom on the rendered document.
- `toolbarActions` is a snippet.
