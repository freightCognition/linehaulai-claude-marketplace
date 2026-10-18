<!--
	File tree (FileSystem) + preview pane, with a Group/ToggleGroup toolbar and a
	ColorPicker for the highlight color. `items` would normally come from a
	+page.server.ts listing an S3/R2 bucket; URLs are resolved lazily through
	getFileUrl. Registry copy-in: swap imports for '$lib/components/<name>/index.js'.
-->
<script lang="ts">
	import {
		FileSystem,
		FileThumbnail,
		PdfViewer,
		Group,
		GroupText,
		ToggleGroup,
		ToggleGroupItem,
		ColorPicker
	} from 'extend-ui-svelte';
	import type { FileSystemFileItem, FileSystemItem } from 'extend-ui-svelte/components/file-system';

	let { isDark = false }: { isDark?: boolean } = $props();

	const items: FileSystemItem[] = [
		{ kind: 'folder', path: 'invoices/' },
		{ kind: 'file', path: 'invoices/2026/jan.pdf', contentType: 'application/pdf', size: 182_311 },
		{ kind: 'file', path: 'invoices/2026/feb.pdf', contentType: 'application/pdf', size: 201_004 },
		{ kind: 'file', path: 'scans/receipt.png', contentType: 'image/png', url: '/files/scans/receipt.png' },
		{ kind: 'file', path: 'readme.txt', contentType: 'text/plain' }
	];

	let selectedPath = $state<string | null>(null);
	let opened = $state<{ file: FileSystemFileItem; url: string } | null>(null);
	let openError = $state<string | null>(null);
	let layout = $state<string[]>(['split']);
	let highlight = $state('#facc15');

	const selectedFile = $derived(
		items.find((item): item is FileSystemFileItem => item.kind === 'file' && item.path === selectedPath) ?? null
	);

	// Called only when a file has no `url`. May return a promise (e.g. a presigned URL).
	async function getFileUrl(file: FileSystemFileItem): Promise<string> {
		const res = await fetch(`/api/files/presign?key=${encodeURIComponent(file.key ?? file.path)}`);
		if (!res.ok) throw new Error(`presign failed: ${res.status}`);
		return ((await res.json()) as { url: string }).url;
	}

	function onFileOpen(file: FileSystemFileItem, url: string | null) {
		// url is null when getFileUrl threw or was not provided.
		openError = url ? null : `Could not resolve a URL for ${file.path}`;
		opened = url ? { file, url } : null;
	}

	const kindOf = (file: FileSystemFileItem) =>
		file.contentType === 'application/pdf' || file.path.endsWith('.pdf')
			? 'pdf'
			: file.contentType?.startsWith('image/')
				? 'image'
				: 'other';
</script>

<div class="grid gap-3">
	<Group aria-label="Viewer toolbar">
		<GroupText>Layout</GroupText>
		<ToggleGroup
			spacing="none"
			aria-label="Layout"
			value={layout}
			onValueChange={(next, details) => (next.length ? (layout = next) : details.cancel())}
		>
			<ToggleGroupItem value="split" variant="outline">Split</ToggleGroupItem>
			<ToggleGroupItem value="viewer" variant="outline">Viewer only</ToggleGroupItem>
		</ToggleGroup>
	</Group>

	<div class="flex items-center gap-2 text-sm">
		<span>Highlight</span>
		<ColorPicker variant="swatch" value={highlight} onChange={(hex) => (highlight = hex)} label="Highlight color" />
		<code>{highlight}</code>
	</div>

	<div class={layout[0] === 'split' ? 'grid grid-cols-[18rem_1fr] gap-4' : 'grid'}>
		{#if layout[0] === 'split'}
			<aside class="grid content-start gap-3">
				<FileSystem
					{items}
					title="Documents"
					defaultPath="invoices/2026/"
					bind:selectedPath
					{getFileUrl}
					{onFileOpen}
					renamable={false}
					{isDark}
				/>

				{#if selectedFile}
					<!-- Single-click preview; double-click or Enter opens the full viewer. -->
					<div class="w-40">
						<FileThumbnail
							file={{ name: selectedFile.path, type: selectedFile.contentType ?? '' }}
							pdfUrl={kindOf(selectedFile) === 'pdf' ? (selectedFile.url ?? null) : null}
							previewImageUrl={kindOf(selectedFile) === 'image' ? (selectedFile.url ?? null) : null}
							width={160}
							{isDark}
						/>
					</div>
				{/if}
			</aside>
		{/if}

		<main class="min-h-[60vh]" style:--highlight={highlight}>
			{#if openError}
				<p role="alert">{openError}</p>
			{:else if !opened}
				<p>Double-click a file (or press Enter) to open it.</p>
			{:else if kindOf(opened.file) === 'pdf'}
				<PdfViewer src={opened.url} fileName={opened.file.name ?? opened.file.path} {isDark} />
			{:else if kindOf(opened.file) === 'image'}
				<img src={opened.url} alt={opened.file.path} class="max-h-[70vh] object-contain" />
			{:else}
				<!-- DOCX/XLSX/CSV/PPTX: route to the matching viewer from the extend-ui-viewers skill. -->
				<a href={opened.url} download>Download {opened.file.path}</a>
			{/if}
		</main>
	</div>
</div>
