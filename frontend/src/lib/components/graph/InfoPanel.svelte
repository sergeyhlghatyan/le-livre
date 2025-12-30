<script lang="ts">
	import Button from '$lib/components/ui/Button.svelte';
	import type { GraphNode } from '$lib/api';

	interface NodeMetadata {
		hasChildren: boolean;
		childrenLoaded: boolean;
		childCount: number;
	}

	interface Props {
		node: GraphNode | null;
		year: number;
		nodeMetadata: Map<string, NodeMetadata>;
		expandedNodes: Set<string>;
		loadingChildren: Set<string>;
		onNavigate: (nodeId: string) => void;
		onExpand: (nodeId: string) => void;
		onCollapse: (nodeId: string) => void;
		onClose: () => void;
	}

	let { node, year, nodeMetadata, expandedNodes, loadingChildren, onNavigate, onExpand, onCollapse, onClose }: Props = $props();

	const metadata = $derived(node ? nodeMetadata.get(node.id) : null);
	const isExpanded = $derived(node ? expandedNodes.has(node.id) : false);
	const isLoading = $derived(node ? loadingChildren.has(node.id) : false);
	const canExpand = $derived(metadata?.hasChildren && !metadata.childrenLoaded);
	const canCollapse = $derived(metadata?.hasChildren && metadata.childrenLoaded);

	const levelColors: Record<string, string> = {
		section: '#3B82F6',
		subsection: '#10B981',
		paragraph: '#F59E0B',
		subparagraph: '#8B5CF6',
		clause: '#EC4899'
	};
</script>

{#if node}
	<div
		class="absolute top-4 right-4 w-80 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg shadow-xl overflow-hidden"
	>
		<!-- Header -->
		<div class="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
			<h3 class="text-sm font-medium text-neutral-900 dark:text-neutral-50">Node Details</h3>
			<button
				onclick={onClose}
				class="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 transition-colors"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="p-4 space-y-4 max-h-96 overflow-y-auto">
			<!-- Provision Number -->
			<div>
				<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Provision</div>
				<div class="text-sm font-medium text-neutral-900 dark:text-neutral-50 font-mono">
					{node.label}
				</div>
			</div>

			<!-- Level -->
			<div>
				<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Level</div>
				<div class="flex items-center gap-2">
					<div
						class="w-3 h-3 rounded-full"
						style="background-color: {levelColors[node.level] || '#6B7280'}; box-shadow: 0 0 0 2px {levelColors[node.level] || '#6B7280'}33;"
					></div>
					<span class="text-sm text-neutral-700 dark:text-neutral-300 capitalize">{node.level}</span>
				</div>
			</div>

			<!-- Heading -->
			{#if node.heading}
				<div>
					<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Heading</div>
					<div class="text-sm text-neutral-700 dark:text-neutral-300">
						{node.heading}
					</div>
				</div>
			{/if}

			<!-- Year -->
			<div>
				<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Year</div>
				<div class="text-sm text-neutral-700 dark:text-neutral-300">{year}</div>
			</div>

			<!-- Provision ID -->
			<div>
				<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Full ID</div>
				<div class="text-xs text-neutral-600 dark:text-neutral-400 font-mono break-all">
					{node.id}
				</div>
			</div>

			<!-- Expand/Collapse Section -->
			{#if metadata?.hasChildren}
				<div class="pt-2 border-t border-neutral-200 dark:border-neutral-700">
					<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
						Children ({metadata.childCount})
					</div>

					{#if canExpand}
						<Button
							variant="secondary"
							onclick={() => onExpand(node.id)}
							disabled={isLoading}
							class="w-full"
						>
							{#if isLoading}
								<svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								Loading...
							{:else}
								<svg class="mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
								</svg>
								Expand Children ({metadata.childCount})
							{/if}
						</Button>
					{:else if canCollapse}
						<Button
							variant="ghost"
							onclick={() => onCollapse(node.id)}
							class="w-full"
						>
							<svg class="mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
							</svg>
							Collapse Children
						</Button>
					{/if}
				</div>
			{/if}

			<!-- Action Button -->
			<div class="pt-2">
				<Button
					variant="primary"
					onclick={() => onNavigate(node.id)}
					class="w-full"
				>
					View Full Provision
				</Button>
			</div>
		</div>
	</div>
{/if}
