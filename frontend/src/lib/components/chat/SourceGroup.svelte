<script lang="ts">
	import { slide } from 'svelte/transition';
	import SourceCard from './SourceCard.svelte';
	import type { Source } from '$lib/api';

	interface Props {
		title: string;
		sources: Source[];
		variant: 'semantic' | 'graph' | 'both';
		defaultExpanded?: boolean;
	}

	let { title, sources, variant, defaultExpanded = true }: Props = $props();

	let expanded = $state(defaultExpanded);
	let showAll = $state(false);

	// Progressive disclosure - show 2 sources initially, then all
	const displayedSources = $derived(showAll ? sources : sources.slice(0, 2));
	const remainingCount = $derived(sources.length - displayedSources.length);

	// Variant-specific styles
	const styles = $derived(() => {
		const variantStyles = {
			semantic: {
				border: 'border-l-blue-500',
				bg: 'bg-blue-50 dark:bg-blue-950/20',
				text: 'text-blue-700 dark:text-blue-300',
				badge: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
			},
			graph: {
				border: 'border-l-purple-500',
				bg: 'bg-purple-50 dark:bg-purple-950/20',
				text: 'text-purple-700 dark:text-purple-300',
				badge: 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
			},
			both: {
				border: 'border-l-blue-500', // Using blue as base (gradient requires pseudo-element)
				bg: 'bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-950/10 dark:to-purple-950/10',
				text: 'text-blue-700 dark:text-blue-300', // Fallback for gradient text
				badge: 'border border-blue-500 bg-white dark:bg-neutral-950 text-neutral-700 dark:text-neutral-300'
			}
		};
		return variantStyles[variant];
	});

	// Unique ID for ARIA
	const groupId = `source-group-${variant}-${Math.random().toString(36).substr(2, 9)}`;

	function toggleExpanded() {
		expanded = !expanded;
	}

	function toggleShowAll() {
		showAll = !showAll;
	}
</script>

<!-- Group container with accent bar -->
<div class="mb-4 rounded-lg border-l-4 {styles().border} bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 overflow-hidden">
	<!-- Header: clickable to toggle expand/collapse -->
	<button
		type="button"
		onclick={toggleExpanded}
		aria-expanded={expanded}
		aria-controls="{groupId}-content"
		aria-label="{title}, {sources.length} sources, {expanded ? 'expanded' : 'collapsed'}"
		class="w-full flex items-center justify-between p-3 {styles().bg} hover:opacity-90 transition-opacity cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
	>
		<div class="flex items-center gap-3">
			<!-- Chevron icon -->
			<span
				class="text-xs transform transition-transform duration-200 {expanded ? 'rotate-90' : ''} {styles().text}"
			>
				▶
			</span>

			<!-- Title -->
			<span class="font-medium text-sm {styles().text}">
				{title}
			</span>

			<!-- Count badge -->
			<span class="text-xs px-2 py-0.5 rounded-full {styles().badge} font-medium">
				{sources.length}
			</span>
		</div>

		<!-- Optional: Show collapsed indicator -->
		{#if !expanded}
			<span class="text-xs {styles().text} opacity-70">
				Click to expand
			</span>
		{/if}
	</button>

	<!-- Collapsible content -->
	{#if expanded}
		<div
			id="{groupId}-content"
			role="region"
			aria-labelledby="{groupId}-header"
			transition:slide={{ duration: 200 }}
			class="p-4 space-y-2"
		>
			<!-- Display sources (2 or all, based on showAll state) -->
			{#each displayedSources as source}
				<SourceCard {source} {variant} />
			{/each}

			<!-- Show more/less button -->
			{#if remainingCount > 0}
				<button
					type="button"
					onclick={toggleShowAll}
					class="w-full py-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					{showAll ? 'Show less' : `Show ${remainingCount} more source${remainingCount === 1 ? '' : 's'}`}
				</button>
			{/if}
		</div>
	{/if}
</div>
