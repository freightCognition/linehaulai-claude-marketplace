<!--
	Extraction review screen: PDF with bounding-box citations on the left,
	editable extracted fields on the right. Focus a field to jump to and
	highlight its source region; click a box on the page to focus its field.

	Mock data: an invoice extraction result with citations in PDF points
	(612 x 792, US Letter). Replace PDF_URL and RESULT with your backend data.
	Registry copy-in: import from '$lib/components/bounding-box-citations/index.js'.
-->
<script lang="ts">
	import { BoundingBoxCitations } from 'extend-ui-svelte';
	import {
		formatCitationValue,
		type JsonObject,
		type JsonValue,
		type ReviewCitation,
		type ReviewField,
		type ReviewMetadataEntry
	} from 'extend-ui-svelte/components/bounding-box-citations';

	let { isDark = false }: { isDark?: boolean } = $props();

	const PDF_URL = '/documents/inv-20931.pdf';

	/** Rectangle in PDF points to a citation polygon. Page numbers are 1-based. */
	function cite(page: number, left: number, top: number, right: number, bottom: number): ReviewCitation {
		return {
			page,
			pageWidth: 612,
			pageHeight: 792,
			polygon: [
				{ x: left, y: top },
				{ x: right, y: top },
				{ x: right, y: bottom },
				{ x: left, y: bottom }
			]
		};
	}

	// What an extraction API typically returns: values plus per-path citations.
	const RESULT: { value: JsonObject; metadata: Record<string, ReviewMetadataEntry> } = {
		value: {
			invoice_number: 'INV-20931',
			invoice_date: '2026-09-14',
			currency: 'USD',
			total: 1280.5,
			paid: false,
			vendor: { name: 'Blue Ridge Freight LLC', city: 'Asheville', state: 'NC' },
			line_items: [
				{ description: 'Linehaul ATL to CLT', quantity: 1, amount: 1100 },
				{ description: 'Fuel surcharge', quantity: 1, amount: 180.5 }
			]
		},
		metadata: {
			invoice_number: { citations: [cite(1, 420, 72, 560, 90)] },
			invoice_date: { citations: [cite(1, 420, 94, 560, 112)] },
			currency: { citations: [cite(1, 500, 640, 560, 656)] },
			total: { citations: [cite(1, 440, 610, 560, 630)] },
			paid: { citations: [cite(2, 48, 80, 300, 100)] },
			vendor: { citations: [cite(1, 48, 116, 300, 170)] },
			'vendor.name': { citations: [cite(1, 48, 116, 260, 134)] },
			'vendor.city': { citations: [cite(1, 48, 136, 160, 152)] },
			line_items: { citations: [cite(1, 48, 380, 564, 440)] },
			'line_items[0]': { citations: [cite(1, 48, 400, 564, 418)] },
			'line_items[1]': { citations: [cite(1, 48, 420, 564, 438)] }
		}
	};

	// Model output on the left ("actual"); start the editable side from it too.
	// Built once: a new fields array would reset the reviewer's edits.
	const v = RESULT.value;
	const fields: ReviewField[] = [
		{ key: 'invoice_number', schema: { type: 'string', title: 'Invoice number' }, actual: v.invoice_number, expected: v.invoice_number },
		{ key: 'invoice_date', schema: { type: 'string', title: 'Invoice date', description: 'ISO 8601' }, actual: v.invoice_date, expected: v.invoice_date },
		{ key: 'currency', schema: { type: 'string', title: 'Currency', enum: ['USD', 'CAD', 'EUR'] }, actual: v.currency, expected: v.currency },
		{ key: 'total', schema: { type: 'number', title: 'Total' }, actual: v.total, expected: v.total },
		{ key: 'paid', schema: { type: 'boolean', title: 'Marked paid' }, actual: v.paid, expected: v.paid },
		{
			key: 'vendor',
			schema: {
				type: 'object',
				title: 'Vendor',
				properties: {
					name: { type: 'string', title: 'Name' },
					city: { type: 'string', title: 'City' },
					state: { type: 'string', title: 'State' }
				}
			},
			actual: v.vendor,
			expected: v.vendor
		},
		{
			key: 'line_items',
			schema: {
				type: 'array',
				title: 'Line items',
				items: {
					type: 'object',
					properties: {
						description: { type: 'string', title: 'Description' },
						quantity: { type: 'integer', title: 'Qty' },
						amount: { type: 'number', title: 'Amount' }
					}
				}
			},
			actual: v.line_items,
			expected: v.line_items
		}
	];

	let values = $state<JsonObject>();
	let activeFieldKey = $state<string | null>(null);
	let status = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');

	const changed = $derived(
		fields.filter((field) => JSON.stringify(values?.[field.key]) !== JSON.stringify(field.actual))
	);

	// Setting activeFieldKey from outside moves the highlight but does not scroll
	// the PDF; only focus coming from the panel scrolls. So focus the field card
	// (the block marks each one with data-review-field) and let the block do it.
	let root: HTMLElement | undefined = $state();
	function jumpTo(key: string) {
		const card = root?.querySelector<HTMLElement>(`[data-review-field="${CSS.escape(key)}"]`);
		if (card) {
			card.scrollIntoView({ block: 'nearest' });
			card.focus();
		} else {
			activeFieldKey = key;
		}
	}

	function show(value: JsonValue | undefined): string {
		return formatCitationValue(value ?? null);
	}

	async function approve() {
		status = 'saving';
		try {
			const response = await fetch('/api/extractions/inv-20931/review', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ values, corrected: changed.map((field) => field.key) })
			});
			status = response.ok ? 'saved' : 'error';
		} catch {
			status = 'error';
		}
	}
</script>

<header class="review-header">
	<div>
		<h1>Review INV-20931</h1>
		<p>Focused field: <code>{activeFieldKey ?? 'none'}</code></p>
	</div>
	<nav aria-label="Jump to field">
		{#each fields as field (field.key)}
			<button
				type="button"
				aria-pressed={activeFieldKey === field.key}
				onclick={() => jumpTo(field.key)}
			>
				{field.schema.title ?? field.key}
			</button>
		{/each}
	</nav>
</header>

<div bind:this={root}>
	<BoundingBoxCitations
		src={PDF_URL}
		fileName="inv-20931"
		{fields}
		metadata={RESULT.metadata}
		bind:values
		bind:activeFieldKey
		{isDark}
		height={760}
	/>
</div>

<footer class="review-footer">
	{#if changed.length}
		<ul>
			{#each changed as field (field.key)}
				<li>
					<strong>{field.schema.title ?? field.key}</strong>:
					{show(field.actual)} to {show(values?.[field.key])}
				</li>
			{/each}
		</ul>
	{:else}
		<p>No corrections.</p>
	{/if}
	<button type="button" disabled={status === 'saving'} onclick={approve}>
		{changed.length ? `Approve with ${changed.length} correction(s)` : 'Approve'}
	</button>
	{#if status === 'saved'}<p role="status">Saved.</p>{/if}
	{#if status === 'error'}<p role="alert">Could not save the review.</p>{/if}
</footer>

<style>
	.review-header,
	.review-footer {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 0;
	}

	nav {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}

	nav button[aria-pressed='true'] {
		font-weight: 600;
		text-decoration: underline;
	}
</style>
