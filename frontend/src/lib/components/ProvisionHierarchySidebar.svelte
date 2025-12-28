<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	interface HierarchyNode {
		provision_id: string;
		provision_level: string;
		provision_num: string;
		heading?: string;
		children: HierarchyNode[];
	}

	interface Props {
		provisionId: string;
		year: number;
		currentProvisionId: string; // Which provision is currently being viewed
	}

	let { provisionId, year, currentProvisionId }: Props = $props();

	let hierarchy = $state<HierarchyNode | null>(null);
	let loading = $state(true);
	let error = $state('');
	let expandedNodes = $state<Set<string>>(new Set());

	onMount(async () => {
		await loadHierarchy();
	});

	async function loadHierarchy() {
		try {
			const response = await fetch(
				`http://localhost:8000/provisions/hierarchy/${encodeURIComponent(provisionId)}?year=${year}`
			);

			if (!response.ok) {
				throw new Error('Failed to load hierarchy');
			}

			hierarchy = await response.json();

			// Auto-expand nodes in the path to current provision
			if (hierarchy) {
				expandPathToNode(currentProvisionId);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load hierarchy';
		} finally {
			loading = false;
		}
	}

	function expandPathToNode(targetId: string) {
		if (!hierarchy) return;

		// Expand all ancestor nodes of the current provision
		const pathParts = targetId.split('/');
		for (let i = 1; i < pathParts.length; i++) {
			const ancestorId = pathParts.slice(0, i + 1).join('/');
			expandedNodes.add(ancestorId);
		}
	}

	function toggleNode(nodeId: string) {
		if (expandedNodes.has(nodeId)) {
			expandedNodes.delete(nodeId);
		} else {
			expandedNodes.add(nodeId);
		}
		// Trigger reactivity
		expandedNodes = new Set(expandedNodes);
	}

	function navigateToProvision(nodeId: string) {
		goto(`/provision/${encodeURIComponent(nodeId)}?year=${year}`);
	}

	function isCurrentNode(nodeId: string): boolean {
		return nodeId === currentProvisionId;
	}

	function hasChildren(node: HierarchyNode): boolean {
		return node.children.length > 0;
	}

	function isExpanded(nodeId: string): boolean {
		return expandedNodes.has(nodeId);
	}

	// Get display label for a node (provision_num or last part of ID)
	function getNodeLabel(node: HierarchyNode): string {
		if (node.provision_num) return node.provision_num;
		const parts = node.provision_id.split('/');
		return parts[parts.length - 1] || node.provision_id;
	}
</script>

<div class="h-full flex flex-col bg-white dark:bg-neutral-950 border-r border-neutral-200 dark:border-neutral-800">
	<!-- Header -->
	<div class="p-4 border-b border-neutral-200 dark:border-neutral-800">
		<h2 class="text-sm font-medium text-neutral-900 dark:text-neutral-50">Hierarchy</h2>
	</div>

	<!-- Tree Content -->
	<div class="flex-1 overflow-y-auto p-4">
		{#if loading}
			<p class="text-xs text-neutral-500 dark:text-neutral-400">Loading...</p>
		{:else if error}
			<p class="text-xs text-error">{error}</p>
		{:else if hierarchy}
			{@render TreeNode(hierarchy)}
		{/if}
	</div>
</div>

<!-- Tree Node Snippet -->
{#snippet TreeNode(node: HierarchyNode)}
	<div class="space-y-1">
		<!-- Node Button -->
		<button
			type="button"
			onclick={() => {
				if (hasChildren(node)) toggleNode(node.provision_id);
				navigateToProvision(node.provision_id);
			}}
			class="w-full text-left px-2 py-1 text-xs font-mono rounded transition-colors flex items-center gap-2 {isCurrentNode(node.provision_id)
				? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-semibold'
				: 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-50'}"
		>
			<!-- Expand/collapse chevron (only if has children) -->
			{#if hasChildren(node)}
				<span
					class="transform transition-transform duration-200 {isExpanded(node.provision_id) ? 'rotate-90' : ''}"
					onclick={(e) => {
						e.stopPropagation();
						toggleNode(node.provision_id);
					}}
				>
					▶
				</span>
			{:else}
				<span class="w-3"></span>
			{/if}

			<!-- Node label -->
			<span class="flex-1">
				{getNodeLabel(node)}
				{#if node.heading}
					<span class="text-neutral-500 dark:text-neutral-400 font-normal ml-1">
						- {node.heading}
					</span>
				{/if}
			</span>

			<!-- Current indicator -->
			{#if isCurrentNode(node.provision_id)}
				<span class="text-xs text-blue-600 dark:text-blue-400">●</span>
			{/if}
		</button>

		<!-- Children (if expanded) -->
		{#if hasChildren(node) && isExpanded(node.provision_id)}
			<div class="ml-4 border-l border-neutral-200 dark:border-neutral-800 pl-2">
				{#each node.children as child}
					{@render TreeNode(child)}
				{/each}
			</div>
		{/if}
	</div>
{/snippet}
