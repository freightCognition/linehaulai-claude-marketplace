# FileThumbnail

Source: `src/lib/components/file-thumbnail/FileThumbnail.svelte` and `pdf-thumbnail.ts`. A preview tile built from an image URL, a custom snippet, or one PDF page rendered with the shared PDF engine (PDF.js, dynamically imported on the client).

## Imports

```ts
import { FileThumbnail } from 'extend-ui-svelte';
import {
	FileThumbnail, // also the default export of the subpath
	type FileThumbnailProps,
	type ThumbnailFile,
	clampPageNumber,
	DEFAULT_THUMBNAIL_PAGE, // 1
	DEFAULT_THUMBNAIL_WIDTH, // 240
	renderPdfThumbnail,
	renderLoadedPdfThumbnail,
	thumbnailScale,
	type PdfThumbnailRenderOptions,
	type PdfThumbnailRenderResult
} from 'extend-ui-svelte/components/file-thumbnail';
// registry copy-in: '$lib/components/file-thumbnail/index.js' (needs $lib/engines)
```

## Props

No prop is `$bindable`.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `file` | `ThumbnailFile \| File` (`{ name: string; type: string }`) | required | Required by the type for upstream parity. **Not read by the component**, so it never derives a preview from it. |
| `previewImageUrl` | `string \| null` | `null` | Image to show (object, presigned, or public URL). Blur-in reveal. A URL that has already loaded shows instantly on remount. |
| `previewContent` | `Snippet` | none | Custom preview content filling the tile. |
| `pdfUrl` | `string \| null` | `null` | Render one page of this PDF onto a canvas. |
| `pdfFile` | `File \| Blob \| null` | `null` | PDF bytes. Used instead of `pdfUrl` when both are set. |
| `pageNumber` | `number` | `1` | 1-based page. Clamped into the document. |
| `width` | `number` | `240` | Render width in CSS px (multiplied by `devicePixelRatio` for the backing store). It does **not** size the element. |
| `previewAspectRatio` | `number` | `1`, or the page aspect in PDF mode | CSS `aspect-ratio` (width / height) of the preview box. |
| `previewClassName` | `string` | none | Extra class on the inner preview box. |
| `isLoading` | `boolean` | `false` | Force the pulsing loading overlay. |
| `hasError` | `boolean` | `false` | Force the fallback tile. |
| `class` / `className` | `string` | none | Both merged onto the root. |
| `isDark` | `boolean` | `false` | Dark palette. |
| `onIsDarkChange` | `(isDark: boolean) => void` | none | Accepted for parity. Never called. |

## Source precedence and states

- PDF mode is active only when neither `previewImageUrl` nor `previewContent` is set and `pdfUrl` or `pdfFile` is.
- The image and the snippet can both render, with the snippet layered after the image.
- The loading overlay shows when `isLoading` is true, while the image is loading, or while the PDF page renders.
- The fallback (a plain muted tile) shows when not loading and `hasError` is true, the image failed, the PDF failed, or there is no source at all.
- Changing `pdfUrl`, `pdfFile`, `pageNumber`, or `width` re-renders, and stale renders are discarded. The engine is destroyed on unmount.

## PDF helpers (for building your own page strips)

```ts
renderPdfThumbnail(engine: PdfEngine, source: PdfSource, canvas: HTMLCanvasElement, options?: PdfThumbnailRenderOptions): Promise<PdfThumbnailRenderResult>
renderLoadedPdfThumbnail(engine, pageCount: number, canvas, options?): Promise<PdfThumbnailRenderResult> // reuse one load for many pages
clampPageNumber(page: number, pageCount: number): number
thumbnailScale(pageWidth: number, targetWidth: number, dpr?: number): number
// options: { pageNumber?: number; width?: number; dpr?: number }
// result:  { pageCount, pageNumber, width, height }
```

`PdfEngine` and `createPdfEngine` come from the engines module, which the core skill covers.

## Accessibility

The `<img>` has `alt=""` and the overlays are `aria-hidden`. The tile is decorative. Put the file name in visible text or in the `aria-label` of the button that wraps the tile. It renders no interactive elements, so it is safe inside a `<button>`.

## Full example: thumbnail grid for picked files

```svelte
<script lang="ts">
	import { FileThumbnail } from 'extend-ui-svelte';

	let { files, onOpen }: { files: File[]; onOpen: (file: File) => void } = $props();

	// One object URL per image; revoked when the list changes or the component unmounts.
	const imageUrls = $derived(
		new Map(files.filter((f) => f.type.startsWith('image/')).map((f) => [f, URL.createObjectURL(f)]))
	);
	$effect(() => {
		const urls = imageUrls;
		return () => urls.forEach((url) => URL.revokeObjectURL(url));
	});
</script>

<ul class="grid grid-cols-4 gap-3">
	{#each files as file, i (i)}
		<li>
			<button type="button" class="w-full text-left" aria-label={`Open ${file.name}`} onclick={() => onOpen(file)}>
				<FileThumbnail
					{file}
					class="w-full"
					previewImageUrl={imageUrls.get(file) ?? null}
					pdfFile={file.type === 'application/pdf' ? file : null}
					width={240}
				/>
				<span class="block truncate text-xs">{file.name}</span>
			</button>
		</li>
	{/each}
</ul>
```

## Gotchas

- Size the tile from outside, with a wrapper `div` or a global or Tailwind class on `class`. A parent's scoped `<style>` selector does not reach the child's root, so use `:global(...)` if you style with component CSS.
- `width` is resolution only. Match it to roughly the displayed width to avoid blurry or wasteful canvases.
- PDF rendering needs the browser and the engine's PDF.js worker setup (see the core skill). On the server the canvas simply stays in the loading state until hydration.
- `pdfFile` is read with `arrayBuffer()` on every re-render trigger. For many thumbnails of one large PDF, use `renderLoadedPdfThumbnail` with a single engine load.
- Non-image, non-PDF files (DOCX, XLSX) get the fallback unless you pass `previewContent`, for example an extension badge.
