# ESignature reference

Source: `src/lib/components/e-signature/ESignature.svelte`, `sign-pdf.ts`, `index.ts`.

```ts
import { ESignature, ESignatureBlock, type ESignatureProps } from 'extend-ui-svelte';
import {
	clampPage, clampScale, dataUrlToBytes, defaultPlacementForPage, embedSignaturePng,
	ensurePdfExtension, getSignedDownloadFileName, resolvePlacement,
	DEFAULT_POSITION_X, DEFAULT_POSITION_Y, DEFAULT_SCALE, DEFAULT_SIGNATURE_HEIGHT,
	DEFAULT_SIGNATURE_WIDTH, MAX_SCALE, MIN_SCALE,
	type SignaturePlacement, type SignaturePlacementInput
} from 'extend-ui-svelte/components/e-signature';
// Registry copy-in: same names from '$lib/components/e-signature/index.js'
```

How it works: the user draws on a `signature_pad` canvas. "Place signature" stamps the PNG onto the **original** PDF bytes with pdf-lib, and the PDF.js engine re-renders the preview. "Download signed PDF" saves the stamped bytes.

## Props

| Prop | Type | Default | Bindable | Description |
|---|---|---|---|---|
| `file` | `string` | — | | PDF URL (upstream prop). Fetched with `fetch` on the client. Empty shows "Choose a PDF to sign". |
| `src` | `string` | — | | Alias of `file`. `file` wins when both are set. |
| `fileName` | `string` | derived | | Download base name, saved as `<base>-signed.pdf`. Falls back to the URL basename, then `document`. |
| `page` | `number` | `1` | | **Initial** 1-based page only. The component owns paging after mount. |
| `positionX` | `number` | page-scaled default | **yes** | Left offset in PDF points. |
| `positionY` | `number` | page-scaled default | **yes** | Offset from the **bottom** edge in PDF points. |
| `signatureWidth` | `number` | page-scaled default | **yes** | Box width in pt before scaling. |
| `signatureHeight` | `number` | page-scaled default | **yes** | Box height in pt before scaling. |
| `scale` | `number` | `1` (`DEFAULT_SCALE`) | **yes** | Size multiplier. The slider range is 0.25 to 3. |
| `penColor` | `string` | `'#000000'` | | Ink color. Read once, at mount. |
| `backgroundColor` | `string` | `'rgba(0,0,0,0)'` | | Pad background. Keep it transparent so the stamp has no box. Read once, at mount. |
| `showDownload` | `boolean` | `true` | | Shows "Download signed PDF". |
| `isDark` | `boolean` | `false` | | Parent-controlled theme. |
| `onIsDarkChange` | `(isDark: boolean) => void` | — | | Accepted, never called. |
| `onSignatureChange` | `(hasSignature: boolean) => void` | — | | Fires after a stroke or Clear changes whether the pad has ink. |
| `onDocumentLoadSuccess` | `(numPages: number) => void` | — | | Page count after load. |
| `onPageChange` | `(page: number) => void` | — | | Previous/Next changed the page. |
| `onSignedDownload` | `(fileName: string) => void` | — | | After the signed download. Gives the **name only**, not the bytes. |
| `class` / `className` | `string` | `''` | | Merged together. |

The page-scaled default (`defaultPlacementForPage(w, h)`) is upstream's field `{ x: 300, y: 504, w: 250, h: 58 }` on a 612×792 top-left page, scaled to the actual page and flipped to a bottom-left origin. A bound value left `undefined` keeps following that default.

## Helpers (`sign-pdf.ts`, SSR-safe, pdf-lib is isomorphic)

```ts
interface SignaturePlacement { page: number; x: number; y: number; width: number; height: number } // pt, bottom-left
interface SignaturePlacementInput { page; x; y; width; height; scale; pageCount: number }

resolvePlacement(input): SignaturePlacement   // clamps page into the document, x/y to >= 0, multiplies size by clamped scale
embedSignaturePng(pdfBytes, pngBytes, placement): Promise<Uint8Array> // throws RangeError for a bad page
dataUrlToBytes('data:image/png;base64,...'): Uint8Array               // throws TypeError otherwise
defaultPlacementForPage(pageWidth, pageHeight)
clampPage(page, pageCount)  // 0 when pageCount is 0
clampScale(n)               // NaN falls back to DEFAULT_SCALE
getSignedDownloadFileName(fileName, src)  // "<base>-signed.pdf"
ensurePdfExtension(name)
// Constants: DEFAULT_SIGNATURE_WIDTH 250, DEFAULT_SIGNATURE_HEIGHT 58, DEFAULT_POSITION_X 300,
// DEFAULT_POSITION_Y 230, DEFAULT_SCALE 1, MIN_SCALE 0.25, MAX_SCALE 3
```

## Keyboard

There are no custom shortcuts. Controls are native buttons and inputs: Clear signature, Previous/Next page, Position X/Y (pt), Width/Height (pt), the Scale range, Place signature, and Download signed PDF. Drawing on the pad needs a pointer, so there is no keyboard or typed-signature alternative. For accessibility, offer a typed-name fallback outside the component.

## Snippets

None.

## Example: drop-in, with the placement bound to app state

```svelte
<script lang="ts">
	import { ESignature } from 'extend-ui-svelte';

	let isDark = $state(false);
	let x = $state<number>(72);   // 1 inch from the left
	let y = $state<number>(72);   // 1 inch from the bottom
	let scale = $state(1);
	let signed = $state(false);
	let hasInk = $state(false);
</script>

<ESignature
	file="/api/documents/42/pdf"
	fileName="rate-confirmation-42"
	page={1}
	bind:positionX={x}
	bind:positionY={y}
	bind:scale
	penColor="#1d4ed8"
	{isDark}
	onSignatureChange={(v) => (hasInk = v)}
	onSignedDownload={() => (signed = true)}
/>
<p>Ink: {hasInk ? 'yes' : 'no'} · Placed at ({x}, {y}) pt · {signed ? 'Downloaded' : 'Not downloaded'}</p>
```

To upload the signed PDF instead, see `../examples/sign-and-upload-pdf.svelte`. It skips the component and uses `signature_pad` with `embedSignaturePng`.

## Gotchas

- **No bytes callback.** The component cannot hand the signed PDF to your code. Use the helpers for upload flows.
- Coordinates are PDF points from the bottom-left corner. Convert from screen clicks with `yPt = pageHeightPt - clickYPt`.
- `file` must be a fetchable URL. Use `URL.createObjectURL(file)` for local files, and the URL must be CORS-readable.
- `embedSignaturePng` calls `PDFDocument.load` without `ignoreEncryption`, so encrypted PDFs throw. The component shows the error inline.
- A stamp is a flattened image, not a cryptographic (PAdES) digital signature, and no audit trail is recorded. Add hashing, timestamps, and signer identity on the server if the use is legally binding.
- Re-placing replaces the stamp. Changing `file` drops the stamp and reloads.
- Unmounting loses the drawn signature and the stamped bytes.
- Not ported: the signature dialog, the draggable field overlay, initials/date/checkbox/text fields, recipients, required-field validation, signed/pending/declined states, and the resizable two-pane shell. Upstream's only prop, `file`, is supported.
