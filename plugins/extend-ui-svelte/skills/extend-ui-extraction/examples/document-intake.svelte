<!--
	Document intake screen: split a multi-document PDF into sections, then
	inspect the parsed layout blocks of the selected page with the focused
	block outlined on the PDF.

	Upstream's OcrBlockOverlay is not ported, so the outline is drawn here with
	PdfViewer's pageOverlay snippet and blockToArea. Page numbers are 1-based
	everywhere (split page ids, OcrBlock.page, overlay.pageNumber).
	Registry copy-in: import from '$lib/components/<name>/index.js'.
-->
<script lang="ts">
	import { DocumentSplits, LayoutBlocks, PdfViewer } from 'extend-ui-svelte';
	import {
		createInitialSplits,
		getPageNumber,
		type DocumentSplit
	} from 'extend-ui-svelte/components/document-splits';
	import {
		blockToArea,
		getOcrBlocks,
		type OcrBlock,
		type ParsedOcrOutput
	} from 'extend-ui-svelte/components/layout-blocks';

	let { isDark = false }: { isDark?: boolean } = $props();

	const PDF_URL = '/uploads/packet-4821.pdf';
	const PAGE = { width: 612, height: 792 }; // OCR geometry is in PDF points here

	// Mock parser output. Geometry units must match metadata.page width/height.
	const OCR: ParsedOcrOutput = {
		chunks: [
			{
				blocks: [
					{
						id: 'p1-title',
						type: 'section_heading',
						content: '# INVOICE',
						metadata: { page: { number: 1, ...PAGE }, avgOcrConfidence: 0.99 },
						boundingBox: { left: 48, top: 60, right: 220, bottom: 92 }
					},
					{
						id: 'p1-table',
						type: 'table',
						content:
							'| Description | Amount |\n|---|---|\n| Linehaul ATL to CLT | 1,100.00 |\n| Fuel surcharge | 180.50 |',
						metadata: { page: { number: 1, ...PAGE }, avgOcrConfidence: 0.94 },
						polygon: [
							{ x: 48, y: 380 },
							{ x: 564, y: 380 },
							{ x: 564, y: 440 },
							{ x: 48, y: 440 }
						]
					},
					{
						id: 'p1-footer',
						type: 'footer',
						content: 'Blue Ridge Freight LLC, Asheville NC',
						metadata: { page: { number: 1, ...PAGE }, avgOcrConfidence: 0.97 },
						boundingBox: { left: 48, top: 740, right: 360, bottom: 756 }
					},
					{
						id: 'p2-title',
						type: 'heading',
						content: '## Bill of Lading',
						metadata: { page: { number: 2, ...PAGE }, avgOcrConfidence: 0.98 },
						boundingBox: { left: 48, top: 56, right: 300, bottom: 84 }
					},
					{
						id: 'p2-items',
						type: 'text',
						content: '- 12 pallets, 9,800 lb\n- Class 70',
						metadata: { page: { number: 2, ...PAGE }, layoutClass: 'List Item', avgOcrConfidence: 0.9 },
						boundingBox: { left: 48, top: 200, right: 400, bottom: 250 }
					}
				]
			}
		]
	};

	const allBlocks = getOcrBlocks(OCR);

	let splits = $state<DocumentSplit[]>([]);
	let activePage = $state(1);
	let activeBlock = $state<OcrBlock | undefined>();

	const pageBlocks = $derived(allBlocks.filter((block) => block.page === activePage));
	const activeSplit = $derived(
		splits.find((split) => split.pages.some((id) => getPageNumber(id) === activePage))
	);

	function onDocumentLoaded(pageCount: number) {
		// Seed once from the real page count; never call createInitialSplits(0) (demo data).
		if (splits.length === 0 && pageCount > 0) splits = createInitialSplits(pageCount);
	}

	function selectPage(page: number) {
		activePage = page;
		activeBlock = undefined;
	}
</script>

<div class="intake">
	<section class="splits" aria-label="Document sections">
		<h2>Sections</h2>
		{#if splits.length}
			<DocumentSplits
				{splits}
				{activePage}
				pdfUrl={PDF_URL}
				{isDark}
				onSelectPage={selectPage}
				onSplitsChange={(next) => (splits = next)}
			/>
		{:else}
			<p>Loading pages...</p>
		{/if}
	</section>

	<section class="viewer" aria-label="Source document">
		<PdfViewer
			src={PDF_URL}
			fileName="packet-4821"
			height={720}
			{isDark}
			onDocumentLoadSuccess={onDocumentLoaded}
			onActivePageChange={selectPage}
		>
			{#snippet pageOverlay(overlay)}
				{#if activeBlock && activeBlock.page === overlay.pageNumber}
					<div
						class="block-outline"
						data-block-type={activeBlock.type}
						style={blockToArea(activeBlock, { width: overlay.pageWidth, height: overlay.pageHeight })}
					></div>
				{/if}
			{/snippet}
		</PdfViewer>
	</section>

	<section class="blocks" aria-label="Layout blocks">
		<h2>
			Page {activePage}
			{#if activeSplit}<small>({activeSplit.title})</small>{/if}
		</h2>
		{#key activePage}
			<LayoutBlocks
				blocks={pageBlocks}
				activeBlockId={activeBlock?.id}
				height={660}
				{isDark}
				onBlockFocus={(block) => (activeBlock = block)}
			/>
		{/key}
	</section>
</div>

<style>
	.intake {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr) minmax(0, 1fr);
		gap: 1rem;
	}

	@media (max-width: 1100px) {
		.intake {
			grid-template-columns: minmax(0, 1fr);
		}
	}

	.block-outline {
		position: absolute;
		box-sizing: border-box;
		border: 2px solid rgb(234 88 12 / 0.85);
		background: rgb(234 88 12 / 0.12);
		border-radius: 2px;
	}

	.block-outline[data-block-type='table'] {
		border-color: rgb(22 163 74 / 0.85);
		background: rgb(22 163 74 / 0.12);
	}
</style>
