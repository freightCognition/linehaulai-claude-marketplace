# PptxViewer

Source: `src/lib/components/pptx-viewer/` (`PptxViewer.svelte`, `PptxSlide.svelte`). Rendering uses the pptx engine (`src/lib/engines/pptx`), which wraps `pptx-browser@^4` and draws each slide to a canvas.

```ts
import { PptxViewer, PptxViewerPreview } from 'extend-ui-svelte';
import {
  PptxViewer,
  PptxSlide,
  type PptxViewerProps,
  type PptxViewerPreviewProps
} from 'extend-ui-svelte/components/pptx-viewer';
// registry copy-in: '$lib/components/pptx-viewer/index.js'
```

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `src` | `string` | `undefined` | The deck URL, fetched on the client. Can be an object URL. When empty, the viewer shows the "Upload PowerPoint" prompt. |
| `fileName` | `string` | `undefined` | The toolbar and download name. Falls back to the basename of `src`, then `presentation.pptx`. |
| `showToolbar` | `boolean` | `true` | Toolbar showing the name, slide count, and actions. |
| `showDownload` | `boolean` | `true` | Download button. |
| `showUpload` | `boolean` | `true` | Upload button. Accepts `.pptx` only. |
| `toolbarActions` | `Snippet` | `undefined` | Extra toolbar content. |
| `height` | `number` | `560` | Viewport height in px. |
| `slideHeight` | `number` | `360` | Fixed row height of one slide in px. Used for the windowing math. |
| `slideWidth` | `number` | `960` | Render width passed to the engine. The canvas height follows the aspect ratio. |
| `overscan` | `number` | `DEFAULT_OVERSCAN` (3) | Extra slides rendered above and below the window. |
| `isDark` | `boolean` | `false` | Dark theme for the chrome. Slides themselves are not recolored. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Accepted for contract parity. Never called. |
| `class` / `className` | `string` | `''` | Both are merged. |

There are no load, error, or slide-change callbacks.

## `PptxSlide`

`PptxSlide` is the internal per-slide canvas, exported only from the per-component entry. Its props are `deck: PptxDeck`, `index: number` (zero-based), `slideCount: number`, and `width?: number` (default 960). It is only useful when you load a deck yourself with the engine's `loadDeck`. That function lives in `engines/pptx`, which the npm `exports` map does not expose, so this path works for registry copy-in only: `$lib/engines/pptx/index.js`.

## Keyboard

There are no custom bindings. Slides sit in a `VirtualList` scroll container, and the toolbar buttons are native buttons.

## Full example

```svelte
<script lang="ts">
  import { PptxViewer } from 'extend-ui-svelte/components/pptx-viewer';

  let { src, isDark = false }: { src: string; isDark?: boolean } = $props();
  // Keep slideHeight in step with slideWidth (16:9 at 640px is 360px, plus caption room).
  const slideWidth = 640;
</script>

<PptxViewer
  {src}
  fileName="Q3 review.pptx"
  height={720}
  {slideWidth}
  slideHeight={Math.round((slideWidth * 9) / 16) + 40}
  {isDark}
  showUpload={false}
/>
```

## Gotchas

- **Slide height must match.** `slideHeight` is a fixed row height for windowing. If it is shorter than the rendered slide plus its caption, slides overlap or clip. Size it from `slideWidth` and the deck's aspect ratio.
- **Large decks.** Only the visible window of slides is mounted and rendered. The whole `.pptx` is fetched and parsed up front.
- **Legacy `.ppt` is not supported.** The engine reads only `.pptx`.
- **Errors** show "Unable to display PowerPoint" with the engine or fetch message (`role="alert"`).
- **SSR.** Loading runs in `$effect`. The server renders the loading state when `src` is set.

## Differences from upstream React `PptxViewerPreview`

- Not ported: `defaultZoom` and zoom modes, `defaultThumbnailSidebarOpen` (the thumbnail sidebar), and `initialSlide` (no jump-to-slide).
- Port-only props: `height`, `slideHeight`, `slideWidth`, `overscan`.
- The renderer is `pptx-browser` instead of `@extend-ai/react-pptx`.
- Dark mode is parent-controlled. Upstream follows the app theme.
