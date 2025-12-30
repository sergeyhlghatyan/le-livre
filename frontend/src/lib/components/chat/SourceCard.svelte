<script lang="ts">
	import { goto } from '$app/navigation';
	import { slide } from 'svelte/transition';

	interface Source {
		provision_id: string;
		heading?: string;
		text_content: string;
		year: number;
		source: 'semantic' | 'graph';
		similarity?: number;
		relationship?: string;
		found_via?: string[];  // Array of sources: ['semantic'], ['graph'], or ['semantic', 'graph']
	}

	interface Props {
		source: Source;
		variant?: 'semantic' | 'graph' | 'both';
	}

	let { source, variant = 'semantic' }: Props = $props();

	// Start collapsed by default
	let expanded = $state(false);

	function toggleExpand(e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		expanded = !expanded;
	}

	function navigateToDetail(e: MouseEvent) {
		console.log('Navigating to provision:', source.provision_id, 'year:', source.year);
		e.preventDefault();
		e.stopPropagation();
		goto(`/provision/${encodeURIComponent(source.provision_id)}?year=${source.year}`);
	}

	// Variant-based accent bar color
	const accentBarColor = $derived(() => {
		if (variant === 'semantic') return 'border-l-blue-500';
		if (variant === 'graph') return 'border-l-purple-500';
		return 'border-l-blue-500'; // 'both' defaults to blue
	});
</script>

<div class="source-card border-l-4 {accentBarColor()} border border-neutral-200 dark:border-neutral-700 rounded-lg bg-white dark:bg-neutral-800 overflow-hidden">
	<!-- Compact header (always visible) -->
	<button
		onclick={toggleExpand}
		class="card-header w-full text-left px-4 py-3 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
	>
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3 flex-1">
				<!-- Provision ID and year -->
				<div class="flex items-center gap-2 text-sm font-mono">
					<span class="font-semibold text-neutral-900 dark:text-neutral-100">{source.provision_id}</span>
					<span class="text-neutral-400">•</span>
					<span class="text-neutral-500 dark:text-neutral-400">({source.year})</span>
				</div>

				<!-- Metadata badges -->
				<div class="flex items-center gap-2">
					{#if source.similarity}
						<span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium">
							{(source.similarity * 100).toFixed(0)}% match
						</span>
					{/if}
					{#if source.relationship}
						<span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 font-medium">
							{source.relationship}
						</span>
					{/if}
				</div>
			</div>

			<!-- Chevron icon -->
			<svg
				class="w-5 h-5 text-neutral-500 transition-transform duration-200 {expanded ? 'rotate-180' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
			</svg>
		</div>
	</button>

	<!-- Expanded content (only when expanded) -->
	{#if expanded}
		<div class="card-body border-t border-neutral-200 dark:border-neutral-700 px-4 py-3" transition:slide={{ duration: 200 }}>
			<!-- Heading -->
			{#if source.heading}
				<h4 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">{source.heading}</h4>
			{/if}

			<!-- Text preview (100 chars) -->
			<p class="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed mb-3">
				{source.text_content.substring(0, 100)}...
			</p>

			<!-- Action button -->
			<div class="flex gap-2">
				<button
					onclick={navigateToDetail}
					class="text-xs px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors"
				>
					View Full Details →
				</button>
			</div>
		</div>
	{/if}
</div>
