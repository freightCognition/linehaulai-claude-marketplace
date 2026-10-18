<!--
	Sign a PDF, then download it or upload it to a server.
	ESignature gives no callback with the signed bytes, so this flow uses its
	helpers directly: signature_pad captures the drawing, and embedSignaturePng
	stamps it with pdf-lib.
	With pnpm or another strict installer, add `signature_pad` and `pdf-lib`
	as direct dependencies (extend-ui-svelte already depends on both).
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type SignaturePad from 'signature_pad';
	import {
		dataUrlToBytes,
		defaultPlacementForPage,
		embedSignaturePng,
		getSignedDownloadFileName,
		resolvePlacement
	} from 'extend-ui-svelte/components/e-signature';

	let {
		pdfUrl,
		uploadUrl = '/api/documents/signed'
	}: { pdfUrl: string; uploadUrl?: string } = $props();

	let canvas: HTMLCanvasElement;
	let pad: SignaturePad | null = $state.raw(null);
	let hasInk = $state(false);
	let pdfBytes: Uint8Array | null = $state.raw(null);
	let pageSizes: { width: number; height: number }[] = $state.raw([]);
	let page = $state(1);
	let signed: Uint8Array | null = $state.raw(null);
	let busy = $state(false);
	let message = $state('');

	// signature_pad needs a canvas, so load it on the client only.
	onMount(() => {
		let instance: SignaturePad | null = null;
		let cancelled = false;
		(async () => {
			const { default: Pad } = await import('signature_pad');
			if (cancelled) return;
			// Match the backing store to the CSS size so strokes land under the pointer.
			const ratio = Math.max(window.devicePixelRatio || 1, 1);
			canvas.width = canvas.offsetWidth * ratio;
			canvas.height = canvas.offsetHeight * ratio;
			canvas.getContext('2d')?.scale(ratio, ratio);
			instance = new Pad(canvas, { penColor: '#111827', backgroundColor: 'rgba(0,0,0,0)' });
			instance.addEventListener('endStroke', () => (hasInk = !instance!.isEmpty()));
			pad = instance;
		})();
		return () => {
			cancelled = true;
			instance?.off();
		};
	});

	// Fetch the source PDF and read each page's size in points.
	$effect(() => {
		const url = pdfUrl;
		let cancelled = false;
		signed = null;
		(async () => {
			const res = await fetch(url);
			if (!res.ok) throw new Error(`Could not load PDF (${res.status})`);
			const bytes = new Uint8Array(await res.arrayBuffer());
			const { PDFDocument } = await import('pdf-lib');
			const doc = await PDFDocument.load(bytes);
			if (cancelled) return;
			pdfBytes = bytes;
			pageSizes = doc.getPages().map((p) => p.getSize());
			page = pageSizes.length; // signature lines usually sit on the last page
		})().catch((e: unknown) => (message = e instanceof Error ? e.message : String(e)));
		return () => {
			cancelled = true;
		};
	});

	async function stamp() {
		if (!pad || pad.isEmpty() || !pdfBytes) return;
		busy = true;
		message = '';
		try {
			const size = pageSizes[page - 1] ?? { width: 612, height: 792 };
			// Upstream's default field, scaled to this page (PDF points, bottom-left origin).
			const box = defaultPlacementForPage(size.width, size.height);
			const placement = resolvePlacement({ ...box, page, scale: 1, pageCount: pageSizes.length });
			const png = dataUrlToBytes(pad.toDataURL('image/png'));
			// Stamp the original bytes, so re-stamping replaces the earlier stamp.
			signed = await embedSignaturePng(pdfBytes, png, placement);
		} catch (e) {
			message = e instanceof Error ? e.message : String(e);
		} finally {
			busy = false;
		}
	}

	function signedBlob(): Blob {
		return new Blob([signed as BlobPart], { type: 'application/pdf' });
	}

	function download() {
		if (!signed) return;
		const url = URL.createObjectURL(signedBlob());
		const a = document.createElement('a');
		a.href = url;
		a.download = getSignedDownloadFileName(undefined, pdfUrl);
		a.click();
		URL.revokeObjectURL(url);
	}

	async function upload() {
		if (!signed) return;
		busy = true;
		try {
			const body = new FormData();
			body.append('file', signedBlob(), getSignedDownloadFileName(undefined, pdfUrl));
			const res = await fetch(uploadUrl, { method: 'POST', body });
			message = res.ok ? 'Signed PDF uploaded.' : `Upload failed (${res.status})`;
		} finally {
			busy = false;
		}
	}

	function clear() {
		pad?.clear();
		hasInk = false;
		signed = null;
	}
</script>

<section class="sign">
	<canvas bind:this={canvas} class="pad" aria-label="Signature pad"></canvas>
	<div class="row">
		<button onclick={clear} disabled={!hasInk}>Clear</button>
		<label>
			Page
			<select bind:value={page} disabled={pageSizes.length === 0}>
				{#each pageSizes as _, i (i)}<option value={i + 1}>{i + 1}</option>{/each}
			</select>
		</label>
		<button onclick={stamp} disabled={!hasInk || !pdfBytes || busy}>Place signature</button>
		<button onclick={download} disabled={!signed}>Download</button>
		<button onclick={upload} disabled={!signed || busy}>Upload</button>
	</div>
	{#if message}<p role="status">{message}</p>{/if}
</section>

<style>
	.pad {
		width: 100%;
		max-width: 480px;
		height: 160px;
		border: 1px dashed #9ca3af;
		border-radius: 0.5rem;
		touch-action: none;
	}
	.row {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-top: 0.5rem;
		flex-wrap: wrap;
	}
</style>
