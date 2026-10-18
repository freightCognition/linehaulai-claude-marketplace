# Document viewer sidebar

Source: `src/lib/components/document-viewer-sidebar/`. Three exports work together:
- `DocumentViewerThumbnailSidebar`, the rail.
- `DocumentViewerSidebarSkeleton`, the loading placeholder.
- `useElementWidth` and `useInlineThumbnailSidebar`, the width helpers, from `document-viewer-sidebar.svelte.ts`.

```ts
import {
  DocumentViewerThumbnailSidebar,
  DocumentViewerSidebarSkeleton,
  useElementWidth,
  useInlineThumbnailSidebar
} from 'extend-ui-svelte';
// INLINE_THUMBNAIL_SIDEBAR_MIN_WIDTH (768) is only on the per-component entry:
import { INLINE_THUMBNAIL_SIDEBAR_MIN_WIDTH } from 'extend-ui-svelte/components/document-viewer-sidebar';
// registry copy-in: '$lib/components/document-viewer-sidebar/index.js'
```

## `DocumentViewerThumbnailSidebar` props

| Prop | Type | Default | Description |
|---|---|---|---|
| `children` | `Snippet` | — | **Required.** Your thumbnail list. |
| `inline` | `boolean` | — | **Required.** `true` puts the rail in the layout flow beside the content. `false` makes it an absolute overlay that slides in from the left. |
| `open` | `boolean` | — | **Required.** When closed in inline mode, the rail collapses with `margin-left: -10rem`. When closed in overlay mode, it translates off-screen and stops receiving pointer events. |
| `isDark` | `boolean` | `false` | Dark theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Accepted for the contract. Never called. |
| `class` / `className` | `string` | — | Both are merged. |

The root is an `<aside>` with `data-sidebar-mode="inline|overlay"` and `data-sidebar-open`. It is 10rem wide. Transitions turn on two animation frames after mount, so the first paint does not slide.

## `DocumentViewerSidebarSkeleton` props

| Prop | Type | Default | Description |
|---|---|---|---|
| `inline` | `boolean` | — | **Required.** The skeleton renders **nothing** when this is `false`, matching upstream. |
| `isDark` | `boolean` | `false` | Dark theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | Never called. |
| `class` / `className` | `string` | — | Both are merged. |

## Helpers

- `useElementWidth<T extends HTMLElement>()` returns `{ ref, width }`. `ref` is a Svelte attachment: write `<div {@attach shell.ref}>`. `width` is a reactive getter fed by a `ResizeObserver`, and it keeps the last non-zero value while the element is hidden. Call it during component init, because it uses `$state`.
- `useInlineThumbnailSidebar(width: number): boolean` returns `width >= 768`. Wrap the call in `$derived(...)` so it re-evaluates.

## Layout contract

The element that holds the sidebar and the content must be positioned and use flex. Overlay mode is `position: absolute`, anchored to it:

```css
.viewer { position: relative; display: flex; flex: 1; min-height: 0; overflow: hidden; }
.content { flex: 1; min-width: 0; overflow: auto; }
```

## Full example (docs-site pattern)

```svelte
<script lang="ts">
  import {
    DocumentViewerThumbnailSidebar,
    DocumentViewerSidebarSkeleton,
    useElementWidth,
    useInlineThumbnailSidebar
  } from 'extend-ui-svelte';

  let { pages, isDark = false }: { pages: { id: number; label: string }[]; isDark?: boolean } = $props();
  const shell = useElementWidth<HTMLDivElement>();
  const inline = $derived(useInlineThumbnailSidebar(shell.width));
  let open = $state(true);
  let active = $state(1);
  let loading = $state(false);
</script>

<button type="button" aria-label="Toggle thumbnails" aria-pressed={open} onclick={() => (open = !open)}>Thumbnails</button>

<div class="viewer" {@attach shell.ref}>
  {#if loading}
    <DocumentViewerSidebarSkeleton {inline} {isDark} />
  {:else}
    <DocumentViewerThumbnailSidebar {inline} {open} {isDark}>
      <ul class="thumbs">
        {#each pages as p (p.id)}
          <li>
            <button type="button" aria-current={p.id === active ? 'page' : undefined} onclick={() => (active = p.id)}>
              {p.id}. {p.label}
            </button>
          </li>
        {/each}
      </ul>
    </DocumentViewerThumbnailSidebar>
  {/if}
  <div class="content" tabindex="0">Page {active}</div>
</div>

<style>
  .viewer { position: relative; display: flex; height: 480px; overflow: hidden; }
  .content { flex: 1; min-width: 0; overflow: auto; }
  .thumbs { height: 100%; overflow: auto; margin: 0; padding: 0.75rem; list-style: none; }
</style>
```

## Gotchas

- **Thumbnails, keyboard handling, and scroll syncing are up to you.** The sidebar is only a responsive shell. Give the list a scroll container (`height: 100%; overflow: auto`), because the `<aside>` has `overflow: hidden`.
- **The viewers expose no `goToPage`.** When pairing with `PdfViewer`, drive the active highlight from `onActivePageChange`. Thumbnail clicks cannot scroll the PDF. `DocxViewer` already has its own thumbnail list.
- **Overlay mode only covers the content.** In overlay mode the rail sits above the content and has no backdrop. Close it on selection if that suits your design.

## Differences from upstream React

- `children` is a snippet.
- The Tailwind props `widthClassName` and `closedInlineClassName` are dropped, so the width is fixed at 10rem.
- `class` is accepted alongside `className`.
- The props `isDark` and `onIsDarkChange` are added.
