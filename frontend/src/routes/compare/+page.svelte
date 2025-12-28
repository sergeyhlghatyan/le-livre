<script lang="ts">
	import { api, type CompareHierarchicalResponse, type HierarchyNode } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Breadcrumb, { type BreadcrumbItem } from '$lib/components/ui/Breadcrumb.svelte';
	import KeyboardLegend from '$lib/components/KeyboardLegend.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	let provisionId = $state('/us/usc/t18/s922/a');
	let yearOld = $state(1994);
	let yearNew = $state(2024);
	let granularity = $state<'word' | 'sentence'>('word');
	let viewMode = $state<'split' | 'unified'>('split');
	let loading = $state(false);
	let result = $state<CompareHierarchicalResponse | null>(null);
	let error = $state('');
	let selectedNode = $state<HierarchyNode | null>(null);
	let treeCollapsed = $state(false);
	let showKeyboardLegend = $state(false);

	const breadcrumbItems = $derived<BreadcrumbItem[]>([
		{ label: 'Home', href: '/' },
		{ label: 'Compare', href: undefined },
		...(result ? [{ label: provisionId }] : [])
	]);

	// Scroll containers
	let leftPane: HTMLDivElement;
	let rightPane: HTMLDivElement;
	let treeContainer: HTMLDivElement;

	async function handleCompare() {
		console.log('[Compare Page] ========== Starting comparison ==========');
		console.log('[Compare Page] Provision:', provisionId, 'Years:', yearOld, '->', yearNew, 'Granularity:', granularity);

		if (!provisionId.trim()) {
			console.log('[Compare Page] Empty provision ID, aborting');
			return;
		}

		console.log('[Compare Page] Setting loading = true');
		loading = true;
		error = '';
		result = null;

		try {
			console.log('[Compare Page] Calling api.compareHierarchical...');
			const startTime = Date.now();

			result = await api.compareHierarchical({
				provision_id: provisionId,
				year_old: yearOld,
				year_new: yearNew,
				granularity
			});

			const elapsed = Date.now() - startTime;
			console.log('[Compare Page] API call completed in', elapsed, 'ms');
			console.log('[Compare Page] Result received:', result ? 'success' : 'null');

			// Auto-select root node
			if (result) {
				console.log('[Compare Page] Setting selectedNode to hierarchy_diff...');
				selectedNode = result.hierarchy_diff;
				console.log('[Compare Page] selectedNode set successfully');
			} else {
				console.warn('[Compare Page] Result is null or undefined');
			}
		} catch (err) {
			console.error('[Compare Page] Error caught in try/catch:', err);
			console.error('[Compare Page] Error type:', err instanceof Error ? 'Error' : typeof err);
			console.error('[Compare Page] Error message:', err instanceof Error ? err.message : String(err));
			error = err instanceof Error ? err.message : 'Comparison failed';
			console.log('[Compare Page] Error state set to:', error);
		} finally {
			console.log('[Compare Page] Finally block executing - setting loading = false');
			loading = false;
			console.log('[Compare Page] loading state is now:', loading);
		}

		console.log('[Compare Page] ========== Comparison complete ==========');
	}

	// Synchronized scrolling
	function handleScroll(source: 'left' | 'right') {
		if (source === 'left' && rightPane) {
			rightPane.scrollTop = leftPane.scrollTop;
		} else if (source === 'right' && leftPane) {
			leftPane.scrollTop = rightPane.scrollTop;
		}
	}

	// Tree node selection
	function selectNode(node: HierarchyNode) {
		selectedNode = node;
	}

	// Flatten tree for navigation
	function* flattenTree(node: HierarchyNode): Generator<HierarchyNode> {
		yield node;
		for (const child of node.children) {
			yield* flattenTree(child);
		}
	}

	const allNodes = $derived(result ? Array.from(flattenTree(result.hierarchy_diff)) : []);
	const changedNodes = $derived(allNodes.filter((n) => n.status !== 'unchanged'));

	// Change progress counter
	const currentChangeIndex = $derived(() => {
		if (!selectedNode || changedNodes.length === 0) return 0;
		const index = changedNodes.indexOf(selectedNode);
		return index >= 0 ? index + 1 : 0;
	});

	// Breadcrumb path for selected node
	const selectedNodePath = $derived(() => {
		if (!selectedNode) return '';
		// Parse provision_id like "/us/usc/t18/s922/a/1" into readable parts
		const parts = selectedNode.provision_id.split('/').filter(p => p);
		const readable = parts.map(part => {
			if (part.startsWith('t')) return `Title ${part.substring(1)}`;
			if (part.startsWith('s')) return `§ ${part.substring(1)}`;
			return `(${part})`;
		});
		return readable.join(' > ');
	});

	function nextChange() {
		if (!selectedNode || changedNodes.length === 0) return;
		const currentIndex = changedNodes.indexOf(selectedNode);
		const nextIndex = (currentIndex + 1) % changedNodes.length;
		selectedNode = changedNodes[nextIndex];
	}

	function prevChange() {
		if (!selectedNode || changedNodes.length === 0) return;
		const currentIndex = changedNodes.indexOf(selectedNode);
		const prevIndex = (currentIndex - 1 + changedNodes.length) % changedNodes.length;
		selectedNode = changedNodes[prevIndex];
	}

	// Keyboard navigation
	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'j' || e.key === 'J') {
			nextChange();
		} else if (e.key === 'k' || e.key === 'K') {
			prevChange();
		} else if (e.key === '?') {
			showKeyboardLegend = true;
		}
	}

	// Auto-scroll tree to selected node
	$effect(() => {
		if (selectedNode && treeContainer) {
			// Find the button element for the selected node in the tree
			const nodeButton = treeContainer.querySelector(
				`button[data-provision-id="${selectedNode.provision_id}"]`
			);

			if (nodeButton) {
				nodeButton.scrollIntoView({
					behavior: 'smooth',
					block: 'nearest',
					inline: 'nearest'
				});
			}
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="flex flex-col h-full">
	<!-- Header -->
	<div class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-6 py-3">
		<Breadcrumb items={breadcrumbItems} />
		<div class="flex items-center justify-between mt-3">
			<div class="flex flex-col gap-2">
				<h1 class="text-lg font-medium text-neutral-900 dark:text-neutral-50">
					{#if result}
						{provisionId} • {yearOld} vs {yearNew}
					{:else}
						Compare
					{/if}
				</h1>
				{#if selectedNode && selectedNodePath()}
					<div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
						{selectedNodePath()}
					</div>
				{/if}
			</div>

			{#if result}
				<div class="flex items-center gap-2">
					<!-- View Toggle -->
					<div class="flex border border-neutral-300 dark:border-neutral-700 rounded-md overflow-hidden">
						<button
							onclick={() => (viewMode = 'split')}
							class="px-3 py-1 text-xs {viewMode === 'split'
								? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50'
								: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50'} transition-colors"
						>
							Split
						</button>
						<button
							onclick={() => (viewMode = 'unified')}
							class="px-3 py-1 text-xs {viewMode === 'unified'
								? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50'
								: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50'} transition-colors"
						>
							Unified
						</button>
					</div>

					<!-- Granularity Toggle -->
					<div class="flex border border-neutral-300 dark:border-neutral-700 rounded-md overflow-hidden">
						<button
							onclick={() => (granularity = 'sentence')}
							class="px-3 py-1 text-xs {granularity === 'sentence'
								? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50'
								: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50'} transition-colors"
						>
							Sentence
						</button>
						<button
							onclick={() => (granularity = 'word')}
							class="px-3 py-1 text-xs {granularity === 'word'
								? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50'
								: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50'} transition-colors"
						>
							Word
						</button>
					</div>

					<!-- Navigation with Counter -->
					<Button variant="ghost" onclick={prevChange}>← Prev</Button>
					{#if changedNodes.length > 0}
						<span class="text-xs text-neutral-600 dark:text-neutral-400 font-medium">
							Change {currentChangeIndex()} of {changedNodes.length}
						</span>
					{/if}
					<Button variant="ghost" onclick={nextChange}>Next →</Button>

					<!-- Help -->
					<Button variant="ghost" onclick={() => (showKeyboardLegend = true)}>?</Button>

					<!-- Export -->
					<Button variant="ghost">Export</Button>
				</div>
			{/if}
		</div>
	</div>

	{#if !result}
		<!-- Compare Form -->
		<div class="flex-1 overflow-y-auto px-6 py-8">
			<div class="max-w-2xl mx-auto">
				<form
					onsubmit={(e) => {
						e.preventDefault();
						handleCompare();
					}}
					class="space-y-4"
				>
					<div>
						<label class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
							Provision ID
						</label>
						<Input bind:value={provisionId} placeholder="/us/usc/t18/s922/a" />
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
								From Year
							</label>
							<Input type="number" bind:value={yearOld} />
						</div>
						<div>
							<label class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
								To Year
							</label>
							<Input type="number" bind:value={yearNew} />
						</div>
					</div>

					<div>
						<label class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
							Granularity
						</label>
						<div class="flex gap-4">
							<label class="flex items-center gap-2 text-sm cursor-pointer">
								<input
									type="radio"
									bind:group={granularity}
									value="sentence"
									class="text-primary"
								/>
								<span class="text-neutral-700 dark:text-neutral-300">Sentence</span>
							</label>
							<label class="flex items-center gap-2 text-sm cursor-pointer">
								<input
									type="radio"
									bind:group={granularity}
									value="word"
									class="text-primary"
								/>
								<span class="text-neutral-700 dark:text-neutral-300">Word</span>
							</label>
						</div>
					</div>

					<Button type="submit" variant="primary" disabled={loading || !provisionId.trim()}>
						{loading ? 'Comparing...' : 'Compare Versions'}
					</Button>
				</form>

				{#if error}
					<div class="mt-6 p-4 border border-error rounded-lg bg-white dark:bg-neutral-950 text-error text-sm">
						{error}
					</div>
				{/if}
			</div>
		</div>

		<!-- Loading Overlay -->
		{#if loading}
			<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
				<div class="bg-white dark:bg-neutral-900 rounded-lg p-8 flex flex-col items-center gap-4 max-w-md mx-4">
					<div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
					<div class="text-center">
						<h3 class="text-base font-medium text-neutral-900 dark:text-neutral-50 mb-2">
							Comparing Provisions
						</h3>
						<p class="text-sm text-neutral-500 dark:text-neutral-400">
							Analyzing hierarchical differences between {yearOld} and {yearNew}...
						</p>
						<p class="text-xs text-neutral-400 dark:text-neutral-500 mt-2">
							This may take 15-30 seconds for complex provisions
						</p>
					</div>
				</div>
			</div>
		{/if}
	{:else}
		<!-- 3-Column Layout -->
		<div class="flex-1 flex overflow-hidden">
			<!-- Tree Column (Collapsible) -->
			{#if !treeCollapsed}
				<div bind:this={treeContainer} class="w-64 flex-shrink-0 border-r border-neutral-200 dark:border-neutral-800 overflow-y-auto bg-white dark:bg-neutral-950">
					<div class="p-4">
						<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-3">
							{changedNodes.length} changes
						</div>
						{@render TreeNav(result.hierarchy_diff, selectedNode, selectNode)}
					</div>
				</div>
			{/if}

			<!-- Diff Panes -->
			{#if viewMode === 'split'}
				<div class="flex-1 flex">
					<!-- Left (Old) -->
					<div class="flex-1 overflow-y-auto" bind:this={leftPane} onscroll={() => handleScroll('left')}>
						<div class="p-6">
							<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-4">{yearOld}</div>
							{#if selectedNode}
								{@render DiffText(selectedNode, 'old')}
							{/if}
						</div>
					</div>

					<!-- Divider -->
					<div class="w-px bg-neutral-200 dark:bg-neutral-800"></div>

					<!-- Right (New) -->
					<div class="flex-1 overflow-y-auto" bind:this={rightPane} onscroll={() => handleScroll('right')}>
						<div class="p-6">
							<div class="text-xs text-neutral-500 dark:text-neutral-400 mb-4">{yearNew}</div>
							{#if selectedNode}
								{@render DiffText(selectedNode, 'new')}
							{/if}
						</div>
					</div>
				</div>
			{:else}
				<!-- Unified View -->
				<div class="flex-1 overflow-y-auto">
					<div class="p-6 max-w-document mx-auto">
						{#if selectedNode}
							{@render UnifiedDiff(selectedNode)}
						{/if}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Tree Navigation Component -->
{#snippet TreeNav(node: HierarchyNode, selectedNode: HierarchyNode | null, selectNode: (node: HierarchyNode) => void)}
	<div class="space-y-1">
		<button
			data-provision-id={node.provision_id}
			onclick={() => selectNode(node)}
			class="w-full text-left px-2 py-1 text-xs font-mono rounded {selectedNode === node
				? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50'
				: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50'} transition-colors"
		>
			<span class={node.status === 'modified'
					? 'text-warning'
					: node.status === 'added'
						? 'text-success'
						: node.status === 'removed'
							? 'text-error'
							: 'text-neutral-400'}>
				{node.provision_id}
			</span>
		</button>
		{#if node.children.length > 0}
			<div class="ml-3 border-l border-neutral-200 dark:border-neutral-800 pl-2">
				{#each node.children as child}
					{@render TreeNav(child, selectedNode, selectNode)}
				{/each}
			</div>
		{/if}
	</div>
{/snippet}

<!-- Diff Text Component -->
{#snippet DiffText(node: HierarchyNode, side: 'old' | 'new')}
	{@const text = side === 'old' ? node.old_text : node.new_text}
	{@const diff = node.inline_diff?.[granularity]}

	{#if text}
		<div class="text-sm font-mono leading-relaxed whitespace-pre-wrap">
			{#if diff && diff.length > 0}
				{#each diff as segment}
					{#if segment.type === 'unchanged'}
						<span class="text-neutral-900 dark:text-neutral-50">{segment.text}</span>
					{:else if segment.type === 'removed' && side === 'old'}
						<span class="bg-red-100 dark:bg-red-900/30 text-error">{segment.text}</span>
					{:else if segment.type === 'added' && side === 'new'}
						<span class="bg-green-100 dark:bg-green-900/30 text-success">{segment.text}</span>
					{/if}
				{/each}
			{:else}
				<span class="text-neutral-900 dark:text-neutral-50">{text}</span>
			{/if}
		</div>
	{:else}
		<div class="text-xs text-neutral-400 dark:text-neutral-600 italic">
			{side === 'old' ? 'Not present in old version' : 'Not present in new version'}
		</div>
	{/if}
{/snippet}

<!-- Unified Diff Component -->
{#snippet UnifiedDiff(node: HierarchyNode)}
	{@const diff = node.inline_diff?.[granularity]}

	<div class="text-sm font-mono leading-relaxed">
		{#if diff && diff.length > 0}
			{#each diff as segment}
				{#if segment.type === 'unchanged'}
					<div class="text-neutral-900 dark:text-neutral-50">{segment.text}</div>
				{:else if segment.type === 'removed'}
					<div class="bg-red-100 dark:bg-red-900/30 text-error">- {segment.text}</div>
				{:else if segment.type === 'added'}
					<div class="bg-green-100 dark:bg-green-900/30 text-success">+ {segment.text}</div>
				{/if}
			{/each}
		{:else}
			<div class="text-neutral-900 dark:text-neutral-50">
				{node.old_text || node.new_text || 'No changes'}
			</div>
		{/if}
	</div>
{/snippet}

<!-- Keyboard Legend Modal -->
<KeyboardLegend open={showKeyboardLegend} onClose={() => (showKeyboardLegend = false)} />
