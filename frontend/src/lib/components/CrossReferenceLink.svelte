<script lang="ts">
	import { goto } from '$app/navigation';
	import type { ParsedReference } from '$lib/utils/reference-parser';
	import { getProvisionIdFromReference } from '$lib/utils/reference-parser';
	import { navigationStore } from '$lib/stores/navigation.svelte';
	import { cachedApi } from '$lib/cache';

	interface Props {
		reference: ParsedReference;
		currentYear?: number;
		currentProvisionHeading?: string;
	}

	let { reference, currentYear = 2024, currentProvisionHeading = '' }: Props = $props();

	// State
	let isHovering = $state(false);
	let previewData = $state<{ heading: string; text: string; isContainer?: boolean } | null>(null);
	let isLoadingPreview = $state(false);
	let hoverTimeout: number | null = null;

	// Computed
	const targetInfo = $derived(getProvisionIdFromReference(reference, currentYear));

	/**
	 * Extract section number from provision ID for display
	 */
	function extractSectionFromProvisionId(provisionId: string): string {
		const match = provisionId.match(/s(\d+)/);
		return match ? `Section ${match[1]}` : provisionId;
	}

	/**
	 * Handle mouse enter - start debounced preview fetch
	 */
	function handleMouseEnter() {
		isHovering = true;

		// Debounce 300ms
		hoverTimeout = window.setTimeout(() => {
			fetchPreview();
		}, 300);
	}

	/**
	 * Handle mouse leave - cancel preview fetch
	 */
	function handleMouseLeave() {
		isHovering = false;

		// Cancel debounce timer
		if (hoverTimeout !== null) {
			clearTimeout(hoverTimeout);
			hoverTimeout = null;
		}

		// Clear preview after a delay (keep it visible briefly)
		setTimeout(() => {
			if (!isHovering) {
				previewData = null;
			}
		}, 200);
	}

	/**
	 * Fetch provision preview from API
	 */
	async function fetchPreview() {
		if (!targetInfo) return;

		isLoadingPreview = true;

		try {
			const data = await cachedApi.getProvisionPreview(targetInfo.provisionId, targetInfo.year);

			// Only update preview if still hovering
			if (isHovering) {
				previewData = {
					heading: data.heading,
					text: data.text_content.slice(0, 200),
					isContainer: false
				};
			}
		} catch (error: any) {
			// Handle 404 gracefully - provision might be a parent-only container
			if (error.message?.includes('Provision not found (404)')) {
				// Show fallback message for container provisions
				if (isHovering) {
					previewData = {
						heading: extractSectionFromProvisionId(targetInfo.provisionId),
						text: 'This section has no text content. It may contain child provisions.',
						isContainer: true
					};
				}
			} else {
				// Only log non-404 errors
				console.error('Failed to fetch provision preview:', error);
			}
		} finally {
			isLoadingPreview = false;
		}
	}

	/**
	 * Handle click - navigate to provision and update breadcrumb stack
	 */
	function handleClick(event: MouseEvent) {
		event.preventDefault();

		if (!targetInfo) return;

		// Add to breadcrumb stack
		navigationStore.push({
			provisionId: targetInfo.provisionId,
			year: targetInfo.year,
			heading: currentProvisionHeading,
			timestamp: Date.now()
		});

		// Navigate to provision
		goto(`/provision/${encodeURIComponent(targetInfo.provisionId)}?year=${targetInfo.year}`);
	}
</script>

<span class="relative inline">
	<a
		href={targetInfo
			? `/provision/${encodeURIComponent(targetInfo.provisionId)}?year=${targetInfo.year}`
			: '#'}
		class="text-blue-600 dark:text-blue-400 underline decoration-dotted hover:decoration-solid cursor-pointer transition-colors"
		on:click={handleClick}
		on:mouseenter={handleMouseEnter}
		on:mouseleave={handleMouseLeave}
	>
		{reference.text}
	</a>

	<!-- Hover preview tooltip -->
	{#if isHovering && (isLoadingPreview || previewData)}
		<div
			class="absolute z-50 bottom-full left-0 mb-2 w-80 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-3"
			on:mouseenter={() => (isHovering = true)}
			on:mouseleave={handleMouseLeave}
		>
			{#if isLoadingPreview}
				<div class="text-sm text-gray-500 dark:text-gray-400">Loading preview...</div>
			{:else if previewData}
				<div class="space-y-2">
					<div class="font-semibold text-sm text-gray-900 dark:text-gray-100">
						{previewData.heading}
					</div>
					<div class="text-xs {previewData.isContainer ? 'italic text-gray-500 dark:text-gray-400' : 'text-gray-600 dark:text-gray-300'} line-clamp-4">
						{previewData.text}
					</div>
					{#if !previewData.isContainer}
						<div class="text-xs text-blue-600 dark:text-blue-400 font-medium">
							Click to navigate →
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</span>
