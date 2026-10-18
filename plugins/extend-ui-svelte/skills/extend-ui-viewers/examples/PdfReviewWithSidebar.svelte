<!--
	PDF review: extracted-field highlights drawn with PdfViewer's pageOverlay
	snippet, plus a responsive DocumentViewerThumbnailSidebar that lists the
	fields and follows the viewer's active page.

	PdfViewer has no goToPage API, so the sidebar cannot scroll the PDF.
	Instead it tracks onActivePageChange and lets the user pick a field to
	emphasise; the overlay highlights the picked field's box.
-->
<script lang="ts">
	import {
		DocumentViewerSidebarSkeleton,
		DocumentViewerThumbnailSidebar,
		PdfViewer,
		useElementWidth,
		useInlineThumbnailSidebar
	} from 'extend-ui-svelte';
	import type { PdfViewerPageOverlayProps } from 'extend-ui-svelte/components/pdf-viewer';

	interface Field {
		id: string;
		label: string;
		value: string;
		page: number;
		/** Box in PDF points at scale 1, top-left origin. */
		box: { x: number; y: number; w: number; h: number };
	}

	let {
		src,
		fields,
		isDark = false
	}: { src: string; fields: Field[]; isDark?: boolean } = $props();

	const shell = useElementWidth<HTMLDivElement>();
	const inline = $derived(useInlineThumbnailSidebar(shell.width));

	let sidebarOpen = $state(true);
	let pageCount = $state(0);
	let activePage = $state(1);
	let activeFieldId = $state<string | null>(null);

	const loaded = $derived(pageCount > 0);
	const fieldsByPage = $derived(
		Array.from({ length: pageCount }, (_, i) => ({
			page: i + 1,
			items: fields.filter((f) => f.page === i + 1)
		})).filter((group) => group.items.length > 0)
	);

	function pick(field: Field): void {
		activeFieldId = field.id;
		// On narrow viewers the sidebar overlays the PDF; get it out of the way.
		if (!inline) sidebarOpen = false;
	}
</script>

<div class="review" class:dark={isDark}>
	<div class="bar">
		<button
			type="button"
			aria-label="Toggle fields"
			aria-pressed={sidebarOpen}
			onclick={() => (sidebarOpen = !sidebarOpen)}
		>
			Fields
		</button>
		<span>{fields.length} extracted fields</span>
	</div>

	<div class="viewer" {@attach shell.ref}>
		{#if !loaded}
			<DocumentViewerSidebarSkeleton {inline} {isDark} />
		{:else}
			<DocumentViewerThumbnailSidebar {inline} open={sidebarOpen} {isDark}>
				<nav class="fields" aria-label="Extracted fields">
					{#each fieldsByPage as group (group.page)}
						<h3 class:current={group.page === activePage}>Page {group.page}</h3>
						<ul>
							{#each group.items as field (field.id)}
								<li>
									<button
										type="button"
										aria-pressed={field.id === activeFieldId}
										onclick={() => pick(field)}
									>
										<span class="label">{field.label}</span>
										<span class="value">{field.value}</span>
									</button>
								</li>
							{/each}
						</ul>
					{/each}
				</nav>
			</DocumentViewerThumbnailSidebar>
		{/if}

		<div class="content">
			<PdfViewer
				{src}
				fileName="review"
				defaultZoom="fit-width"
				height={640}
				{isDark}
				showUpload={false}
				onDocumentLoadSuccess={(n) => (pageCount = n)}
				onActivePageChange={(p) => (activePage = p)}
			>
				{#snippet pageOverlay(o: PdfViewerPageOverlayProps)}
					{#each fields.filter((f) => f.page === o.pageNumber) as field (field.id)}
						<button
							type="button"
							class="highlight"
							class:active={field.id === activeFieldId}
							aria-label={`${field.label}: ${field.value}`}
							style:left="{field.box.x * o.scale}px"
							style:top="{field.box.y * o.scale}px"
							style:width="{field.box.w * o.scale}px"
							style:height="{field.box.h * o.scale}px"
							onclick={() => pick(field)}
						></button>
					{/each}
				{/snippet}
			</PdfViewer>
		</div>
	</div>
</div>

<style>
	.review {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.bar {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}
	/* Sidebar contract: positioned flex parent that clips the overlay rail. */
	.viewer {
		position: relative;
		display: flex;
		min-height: 0;
		overflow: hidden;
	}
	.content {
		flex: 1;
		min-width: 0;
	}
	.fields {
		height: 100%;
		overflow: auto;
		padding: 0.75rem;
		font-size: 12px;
	}
	.fields h3 {
		margin: 0.5rem 0 0.25rem;
		font-size: 11px;
		text-transform: uppercase;
		opacity: 0.6;
	}
	.fields h3.current {
		opacity: 1;
	}
	.fields ul {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.fields button {
		display: grid;
		width: 100%;
		padding: 0.25rem 0.375rem;
		border: 0;
		border-radius: 0.25rem;
		background: transparent;
		color: inherit;
		text-align: left;
		cursor: pointer;
	}
	.fields button[aria-pressed='true'] {
		background: rgb(250 204 21 / 0.25);
	}
	.value {
		opacity: 0.7;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.highlight {
		position: absolute;
		/* PdfViewer's overlay layer is pointer-events: none. */
		pointer-events: auto;
		padding: 0;
		border: 1px solid rgb(202 138 4 / 0.8);
		background: rgb(250 204 21 / 0.2);
		cursor: pointer;
	}
	.highlight.active {
		border-width: 2px;
		background: rgb(250 204 21 / 0.45);
	}
	.review.dark {
		color: #e5e5e5;
	}
</style>
