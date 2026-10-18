<!--
	Universal document viewer: pick a local file or pass a URL, and the right
	extend-ui-svelte viewer renders it. Svelte 5 runes, SSR-safe (all viewers
	load their engines on the client).

	Usage:
	  <UniversalDocumentViewer url="/files/report.pdf" />
	  <UniversalDocumentViewer />   (file picker only)
-->
<script lang="ts">
	import {
		CsvTsvViewer,
		DocxViewer,
		PdfViewer,
		PptxViewer,
		XlsxViewer
	} from 'extend-ui-svelte';
	// Registry copy-in equivalent: import each from '$lib/components/<name>/index.js'.

	type Kind = 'pdf' | 'docx' | 'xlsx' | 'pptx' | 'csv' | 'tsv' | 'unsupported';

	let {
		url = undefined,
		height = 640,
		isDark = $bindable(false)
	}: { url?: string; height?: number; isDark?: boolean } = $props();

	function kindOf(name: string, mime = ''): Kind {
		const ext = (name.split('?')[0] ?? '').split('.').pop()?.toLowerCase() ?? '';
		if (ext === 'pdf' || mime === 'application/pdf') return 'pdf';
		if (ext === 'docx' || mime.includes('wordprocessingml')) return 'docx';
		if (['xlsx', 'xlsm', 'xls', 'ods'].includes(ext) || mime.includes('spreadsheetml')) return 'xlsx';
		if (ext === 'pptx' || mime.includes('presentationml')) return 'pptx';
		if (ext === 'tsv' || mime === 'text/tab-separated-values') return 'tsv';
		if (ext === 'csv' || mime === 'text/csv') return 'csv';
		return 'unsupported';
	}

	let file = $state<File | null>(null);

	// A picked file wins over the url prop.
	const name = $derived(file?.name ?? url ?? '');
	const kind = $derived<Kind | null>(name ? kindOf(name, file?.type) : null);

	// Object URL for viewers that take a string src (PDF, DOCX, PPTX).
	const objectUrl = $derived(file ? URL.createObjectURL(file) : undefined);
	$effect(() => {
		const current = objectUrl;
		return () => {
			if (current) URL.revokeObjectURL(current);
		};
	});
	const src = $derived(objectUrl ?? url);

	// XLSX takes bytes for local files; CSV/TSV take text for both cases.
	let xlsxBytes = $state<ArrayBuffer | undefined>();
	let delimitedText = $state('');
	let loadError = $state('');

	$effect(() => {
		const f = file;
		const u = url;
		const k = kind;
		xlsxBytes = undefined;
		delimitedText = '';
		loadError = '';
		let cancelled = false;
		if (k === 'xlsx' && f) {
			f.arrayBuffer().then((b) => {
				if (!cancelled) xlsxBytes = b;
			});
		} else if (k === 'csv' || k === 'tsv') {
			const read = f
				? f.text()
				: fetch(u as string).then((r) =>
						r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))
					);
			read.then(
				(t) => {
					if (!cancelled) delimitedText = t;
				},
				(e: unknown) => {
					if (!cancelled) loadError = e instanceof Error ? e.message : String(e);
				}
			);
		}
		return () => {
			cancelled = true;
		};
	});

	const setDark = (value: boolean) => (isDark = value);
</script>

<div class="universal" class:dark={isDark}>
	<div class="bar">
		<input
			type="file"
			aria-label="Open a document"
			accept=".pdf,.docx,.xlsx,.xlsm,.xls,.ods,.pptx,.csv,.tsv"
			onchange={(event) => (file = event.currentTarget.files?.[0] ?? null)}
		/>
		<button type="button" aria-pressed={isDark} onclick={() => setDark(!isDark)}>
			{isDark ? 'Light' : 'Dark'}
		</button>
	</div>

	{#if !kind}
		<p class="hint">Choose a PDF, Word, Excel, PowerPoint, CSV, or TSV file.</p>
	{:else if kind === 'pdf'}
		<PdfViewer {src} fileName={name} defaultZoom="fit-width" {height} {isDark} showUpload={false} />
	{:else if kind === 'docx'}
		<DocxViewer {src} fileName={name} defaultZoom="automatic" {isDark} onIsDarkChange={setDark} showUpload={false} />
	{:else if kind === 'xlsx'}
		<XlsxViewer
			src={file ? undefined : url}
			data={xlsxBytes}
			fileName={name}
			{height}
			{isDark}
			onIsDarkChange={setDark}
		/>
	{:else if kind === 'pptx'}
		<PptxViewer {src} fileName={name} {height} {isDark} showUpload={false} />
	{:else if kind === 'csv' || kind === 'tsv'}
		{#if loadError}
			<p class="error" role="alert">Could not read {name}: {loadError}</p>
		{:else}
			<CsvTsvViewer data={delimitedText} delimiter={kind === 'tsv' ? '\t' : ''} search {height} {isDark} />
		{/if}
	{:else}
		<p class="error" role="alert">
			No viewer for “{name}”. Legacy .doc and .ppt files are not supported; convert them to .docx or .pptx.
		</p>
	{/if}
</div>

<style>
	.universal {
		display: grid;
		gap: 0.75rem;
		color: #171717;
	}
	.universal.dark {
		color: #e5e5e5;
	}
	.bar {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	.hint {
		opacity: 0.7;
	}
	.error {
		color: #b91c1c;
	}
	.dark .error {
		color: #f87171;
	}
</style>
