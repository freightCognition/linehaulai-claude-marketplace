<!--
	Load a workbook from an API, track edits, and save the exported .xlsx back.
	XlsxEditor's Export button always triggers a browser download and then
	calls onExport(bytes, fileName). This example uploads in onExport and warns
	before the page unloads with unsaved edits.
-->
<script lang="ts">
	import { beforeNavigate } from '$app/navigation';
	import { XlsxEditor } from 'extend-ui-svelte';
	import {
		columnIndexToLetter,
		type XlsxCellChange
	} from 'extend-ui-svelte/components/xlsx-editor';

	let { workbookId }: { workbookId: string } = $props();

	let isDark = $state(false);
	// Raw state: a new bytes reference resets the editor, so set it once per load.
	let bytes = $state.raw<Uint8Array | undefined>(undefined);
	let loadError = $state('');
	let changes = $state<XlsxCellChange[]>([]);
	let saveStatus = $state('');

	$effect(() => {
		const id = workbookId;
		let cancelled = false;
		bytes = undefined;
		changes = [];
		fetch(`/api/workbooks/${id}`)
			.then(async (res) => {
				if (!res.ok) throw new Error(`Load failed (${res.status})`);
				const data = new Uint8Array(await res.arrayBuffer());
				if (!cancelled) bytes = data;
			})
			.catch((e: unknown) => {
				if (!cancelled) loadError = e instanceof Error ? e.message : String(e);
			});
		return () => {
			cancelled = true;
		};
	});

	function onCellChange(change: XlsxCellChange) {
		changes = [...changes, change];
		saveStatus = '';
	}

	async function onExport(exported: Uint8Array, fileName: string) {
		saveStatus = 'Saving…';
		const body = new FormData();
		body.append(
			'file',
			new Blob([exported as BlobPart], {
				type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
			}),
			fileName
		);
		const res = await fetch(`/api/workbooks/${workbookId}`, { method: 'PUT', body });
		if (res.ok) {
			changes = [];
			saveStatus = 'Saved';
		} else {
			saveStatus = `Save failed (${res.status})`;
		}
	}

	// Edits live only inside the component and vanish on unmount.
	beforeNavigate(({ cancel }) => {
		if (changes.length > 0 && !confirm('Discard unsaved spreadsheet edits?')) cancel();
	});
</script>

<svelte:window
	onbeforeunload={(e) => {
		if (changes.length > 0) e.preventDefault();
	}}
/>

{#if loadError}
	<p role="alert">{loadError}</p>
{:else}
	<XlsxEditor
		data={bytes}
		fileName={`workbook-${workbookId}.xlsx`}
		{isDark}
		onIsDarkChange={(v) => (isDark = v)}
		height={560}
		{onCellChange}
		{onExport}
	/>
{/if}

<p>
	{changes.length} unsaved edit{changes.length === 1 ? '' : 's'}
	{#if changes.length > 0}
		(last: {changes.at(-1)!.sheet}!{columnIndexToLetter(changes.at(-1)!.col)}{changes.at(-1)!.row + 1})
	{/if}
	· Use "Export .xlsx" to save. Bold, alignment, and fill are not written to the file.
	{saveStatus}
</p>
