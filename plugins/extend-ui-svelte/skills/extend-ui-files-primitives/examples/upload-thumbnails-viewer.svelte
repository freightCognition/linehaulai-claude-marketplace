<!--
	Upload -> validate -> thumbnail grid -> open in PdfViewer.
	Drop into a SvelteKit route as +page.svelte. Requires extend-ui-svelte installed
	(see the core extend-ui-svelte skill for PDF engine setup and SSR notes).
	Registry copy-in: swap the imports for '$lib/components/<name>/index.js'.
-->
<script lang="ts">
	import { FileUpload, FileThumbnail, PdfViewer } from 'extend-ui-svelte';
	import { formatBytes } from 'extend-ui-svelte/components/file-upload';

	type Entry = {
		id: string;
		file: File;
		url: string; // our own object URL; FileUpload revokes the ones it hands out
		status: 'uploading' | 'done' | 'error';
	};

	const MAX_BYTES = 15 * 1024 * 1024;
	const MAX_FILES = 12;

	let { isDark = false }: { isDark?: boolean } = $props();
	let entries = $state<Entry[]>([]);
	let errors = $state<string[]>([]);
	let openId = $state<string | null>(null);
	const opened = $derived(entries.find((entry) => entry.id === openId) ?? null);

	function onFilesAccepted(files: File[]) {
		errors = [];
		const room = MAX_FILES - entries.length;
		const fresh: Entry[] = [];
		for (const file of files) {
			if (file.size > MAX_BYTES) {
				errors.push(`${file.name}: larger than ${formatBytes(MAX_BYTES)}`);
			} else if (fresh.length >= room) {
				errors.push(`${file.name}: limit of ${MAX_FILES} files reached`);
			} else {
				fresh.push({
					id: crypto.randomUUID(),
					file,
					url: URL.createObjectURL(file),
					status: 'uploading'
				});
			}
		}
		entries.push(...fresh);
		for (const entry of fresh) void upload(entry.id);
	}

	async function upload(id: string) {
		const entry = entries.find((candidate) => candidate.id === id);
		if (!entry) return;
		const body = new FormData();
		body.append('file', entry.file);
		try {
			const res = await fetch('/api/upload', { method: 'POST', body });
			entry.status = res.ok ? 'done' : 'error';
		} catch {
			entry.status = 'error';
		}
	}

	function remove(id: string) {
		const entry = entries.find((candidate) => candidate.id === id);
		if (entry) URL.revokeObjectURL(entry.url);
		entries = entries.filter((candidate) => candidate.id !== id);
		if (openId === id) openId = null;
	}

	// Revoke every remaining object URL on unmount.
	$effect(() => () => entries.forEach((entry) => URL.revokeObjectURL(entry.url)));

	const isPdf = (file: File) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
	const isImage = (file: File) => file.type.startsWith('image/');
</script>

<section class="grid gap-4">
	<FileUpload
		accept=".pdf,image/png,image/jpeg"
		description={`PDF, PNG or JPG, up to ${formatBytes(MAX_BYTES)} each`}
		acceptedFileTypes={[
			{ label: 'Image', glyph: 'IMG' },
			{ label: 'PDF', glyph: 'PDF' }
		]}
		showFileList={false}
		{isDark}
		{onFilesAccepted}
	/>

	{#if errors.length}
		<ul role="alert" class="text-sm text-red-600">
			{#each errors as error (error)}<li>{error}</li>{/each}
		</ul>
	{/if}

	<ul class="grid grid-cols-2 gap-3 sm:grid-cols-4">
		{#each entries as entry (entry.id)}
			<li class="grid gap-1">
				<button
					type="button"
					class="w-full rounded-lg text-left focus-visible:ring-2"
					aria-label={`Open ${entry.file.name}`}
					aria-pressed={openId === entry.id}
					onclick={() => (openId = entry.id)}
				>
					<FileThumbnail
						file={entry.file}
						class="w-full"
						previewImageUrl={isImage(entry.file) ? entry.url : null}
						pdfFile={isPdf(entry.file) ? entry.file : null}
						previewAspectRatio={3 / 4}
						width={200}
						isLoading={entry.status === 'uploading'}
						hasError={entry.status === 'error'}
						{isDark}
					/>
				</button>
				<div class="flex items-center justify-between gap-2 text-xs">
					<span class="truncate" title={entry.file.name}>{entry.file.name}</span>
					<span>{entry.status === 'done' ? formatBytes(entry.file.size) : entry.status}</span>
				</div>
				<button type="button" class="text-xs underline" onclick={() => remove(entry.id)}>Remove</button>
			</li>
		{/each}
	</ul>

	{#if opened}
		<div class="h-[70vh]">
			{#if isPdf(opened.file)}
				<!-- Other formats: see the extend-ui-viewers skill (DocxViewer, XlsxViewer, CsvViewer). -->
				<PdfViewer src={opened.url} fileName={opened.file.name} {isDark} />
			{:else}
				<img src={opened.url} alt={opened.file.name} class="h-full w-full object-contain" />
			{/if}
		</div>
	{/if}
</section>
