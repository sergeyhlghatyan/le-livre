<script lang="ts">
	import { api, type CompareHierarchicalResponse, type HierarchyNode } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import ToggleGroup from '$lib/components/ui/ToggleGroup.svelte';
	import Breadcrumb, { type BreadcrumbItem } from '$lib/components/ui/Breadcrumb.svelte';
	import KeyboardLegend from '$lib/components/KeyboardLegend.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { ChevronLeft, ChevronRight, Minus, Plus } from 'lucide-svelte';

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
		if (!provisionId.trim()) return;

		loading = true;
		error = '';
		result = null;

		try {
			result = await api.compareHierarchical({
				provision_id: provisionId,
				year_old: yearOld,
				year_new: yearNew,
				granularity
			});

			if (result) {
				selectedNode = result.hierarchy_diff;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Comparison failed';
		} finally {
			loading = false;
		}
	}

	function loadExample(id: string, oldYear: number, newYear: number) {
		provisionId = id;
		yearOld = oldYear;
		yearNew = newYear;
		handleCompare();
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
	{#if !result}
		<!-- Compare Form (Empty State) -->
		<div class="flex-1 overflow-y-auto bg-neutral-50 dark:bg-neutral-900 px-6 py-12">
			<div class="max-w-4xl mx-auto">
				<div class="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-8">
					<!-- Header -->
					<div class="text-center mb-8">
						<h1 class="text-3xl font-bold text-neutral-900 dark:text-neutral-50 mb-3">
							Compare Provision Versions
						</h1>
						<p class="text-neutral-600 dark:text-neutral-400">
							See how provisions have changed across different years
						</p>
					</div>

					<!-- Form -->
					<form
						onsubmit={(e) => {
							e.preventDefault();
							handleCompare();
						}}
						class="space-y-6"
					>
						<div>
							<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								Provision ID
							</label>
							<Input bind:value={provisionId} placeholder="/us/usc/t18/s922/a" />
						</div>

						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
									From Year
								</label>
								<Input type="number" bind:value={yearOld} />
							</div>
							<div>
								<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
									To Year
								</label>
								<Input type="number" bind:value={yearNew} />
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
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

						<Button type="submit" variant="primary" size="lg" disabled={loading || !provisionId.trim()} class="w-full">
							{loading ? 'Comparing...' : 'Compare Versions'}
						</Button>
					</form>

					<!-- Quick Examples -->
					<div class="mt-8 pt-8 border-t border-neutral-200 dark:border-neutral-800">
						<h3 class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-3">Quick Examples:</h3>
						<div class="flex flex-wrap gap-2">
							<button
								onclick={() => loadExample('/us/usc/t18/s922/a', 1994, 2024)}
								class="text-xs px-3 py-2 bg-neutral-100 dark:bg-neutral-800 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
							>
								§ 922(a): 1994 → 2024
							</button>
							<button
								onclick={() => loadExample('/us/usc/t18/s922/d', 2000, 2024)}
								class="text-xs px-3 py-2 bg-neutral-100 dark:bg-neutral-800 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
							>
								§ 922(d): 2000 → 2024
							</button>
						</div>
					</div>

					{#if error}
						<div class="mt-6 p-4 border border-error rounded-lg bg-red-50 dark:bg-red-900/20 text-error text-sm">
							{error}
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Loading Overlay -->
		{#if loading}
			<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
				<div class="bg-white dark:bg-neutral-900 rounded-xl p-8 flex flex-col items-center gap-4 max-w-md mx-4 shadow-lift-lg">
					<div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
					<div class="text-center">
						<h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
							Comparing Provisions
						</h3>
						<p class="text-sm text-neutral-600 dark:text-neutral-400">
							Analyzing hierarchical differences between {yearOld} and {yearNew}...
						</p>
						<p class="text-xs text-neutral-500 dark:text-neutral-500 mt-2">
							This may take 15-30 seconds for complex provisions
						</p>
					</div>
				</div>
			</div>
		{/if}
	{:else}
		<!-- Result View -->
		<!-- Header (Two-Row Layout) -->
		<div class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
			<!-- Row 1: Title and metadata -->
			<div class="px-6 py-4">
				<Breadcrumb items={breadcrumbItems} />
				<div class="flex items-center justify-between mt-3">
					<div>
						<h1 class="text-xl font-bold text-neutral-900 dark:text-neutral-50">
							{provisionId}
						</h1>
						<p class="text-sm text-neutral-600 dark:text-neutral-400">
							{yearOld} vs {yearNew}
						</p>
						{#if selectedNodePath()}
							<p class="text-xs text-neutral-500 dark:text-neutral-500 font-mono mt-1">
								{selectedNodePath()}
							</p>
						{/if}
					</div>
					<Button variant="ghost" onclick={() => result = null}>
						New Comparison
					</Button>
				</div>
			</div>

			<!-- Row 2: Controls -->
			<div class="px-6 py-3 bg-neutral-50 dark:bg-neutral-900 flex items-center justify-between border-t border-neutral-200 dark:border-neutral-800">
				<!-- Left: View controls -->
				<div class="flex items-center gap-4">
					<span class="text-xs font-medium text-neutral-500 dark:text-neutral-400">View:</span>
					<ToggleGroup bind:value={viewMode} options={[
						{ value: 'split', label: 'Split' },
						{ value: 'unified', label: 'Unified' }
					]} />

					<span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 ml-4">Granularity:</span>
					<ToggleGroup bind:value={granularity} options={[
						{ value: 'word', label: 'Word' },
						{ value: 'sentence', label: 'Sentence' }
					]} />
				</div>

				<!-- Right: Navigation -->
				<div class="flex items-center gap-2">
					<Button size="sm" variant="ghost" onclick={prevChange}>
						← Prev
					</Button>
					{#if changedNodes.length > 0}
						<span class="text-xs text-neutral-600 dark:text-neutral-400 font-medium px-2">
							{currentChangeIndex()} / {changedNodes.length}
						</span>
					{/if}
					<Button size="sm" variant="ghost" onclick={nextChange}>
						Next →
					</Button>
					<div class="ml-2 border-l border-neutral-300 dark:border-neutral-700 pl-2">
						<Button size="sm" variant="ghost" onclick={() => (showKeyboardLegend = true)}>
							?
						</Button>
					</div>
				</div>
			</div>
		</div>

		<!-- 3-Column Layout -->
		<div class="flex-1 flex overflow-hidden">
			<!-- Tree Column (Collapsible) -->
			{#if !treeCollapsed}
				<div class="w-64 flex-shrink-0 border-r border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 flex flex-col">
					<div class="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
						<span class="text-xs font-semibold text-neutral-600 dark:text-neutral-400">
							Changes ({changedNodes.length})
						</span>
						<button
							onclick={() => treeCollapsed = true}
							class="p-1 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded transition-colors"
							title="Collapse tree"
						>
							<ChevronLeft class="w-4 h-4 text-neutral-500" />
						</button>
					</div>
					<div bind:this={treeContainer} class="flex-1 overflow-y-auto p-4">
						{@render TreeNav(result.hierarchy_diff, selectedNode, selectNode)}
					</div>
				</div>
			{:else}
				<button
					onclick={() => treeCollapsed = false}
					class="w-10 flex-shrink-0 border-r border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center justify-center transition-colors"
					title="Expand tree"
				>
					<ChevronRight class="w-4 h-4 text-neutral-500" />
				</button>
			{/if}

			<!-- Diff Panes -->
			{#if viewMode === 'split'}
				<div class="flex-1 flex">
					<!-- Left (Old) -->
					<div class="flex-1 overflow-y-auto bg-neutral-50 dark:bg-neutral-950" bind:this={leftPane} onscroll={() => handleScroll('left')}>
						<div class="p-6">
							<div class="text-xs font-semibold text-neutral-500 dark:text-neutral-400 mb-4">{yearOld}</div>
							{#if selectedNode}
								{@render DiffText(selectedNode, 'old')}
							{/if}
						</div>
					</div>

					<!-- Divider -->
					<div class="w-px bg-neutral-300 dark:border-neutral-700"></div>

					<!-- Right (New) -->
					<div class="flex-1 overflow-y-auto bg-neutral-50 dark:bg-neutral-950" bind:this={rightPane} onscroll={() => handleScroll('right')}>
						<div class="p-6">
							<div class="text-xs font-semibold text-neutral-500 dark:text-neutral-400 mb-4">{yearNew}</div>
							{#if selectedNode}
								{@render DiffText(selectedNode, 'new')}
							{/if}
						</div>
					</div>
				</div>
			{:else}
				<!-- Unified View -->
				<div class="flex-1 overflow-y-auto bg-neutral-50 dark:bg-neutral-950">
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
			class="w-full text-left px-2 py-1.5 text-xs font-mono rounded transition-colors {selectedNode === node
				? 'bg-primary text-white'
				: 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-50'}"
		>
			<span class={node.status === 'modified'
					? 'font-semibold'
					: node.status === 'added'
						? 'font-semibold'
						: node.status === 'removed'
							? 'font-semibold'
							: ''}>
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

<!-- Diff Text Component with Accessible Icons -->
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
						<span class="inline-flex items-start gap-1 bg-red-100 dark:bg-red-900/30 text-error px-1 rounded">
							<Minus class="w-3 h-3 flex-shrink-0 mt-0.5" />
							<span>{segment.text}</span>
						</span>
					{:else if segment.type === 'added' && side === 'new'}
						<span class="inline-flex items-start gap-1 bg-green-100 dark:bg-green-900/30 text-success px-1 rounded">
							<Plus class="w-3 h-3 flex-shrink-0 mt-0.5" />
							<span>{segment.text}</span>
						</span>
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

<!-- Unified Diff Component with Icons -->
{#snippet UnifiedDiff(node: HierarchyNode)}
	{@const diff = node.inline_diff?.[granularity]}

	<div class="text-sm font-mono leading-relaxed space-y-1">
		{#if diff && diff.length > 0}
			{#each diff as segment}
				{#if segment.type === 'unchanged'}
					<div class="text-neutral-900 dark:text-neutral-50 py-0.5">{segment.text}</div>
				{:else if segment.type === 'removed'}
					<div class="flex items-start gap-2 bg-red-100 dark:bg-red-900/30 text-error px-2 py-1 rounded">
						<Minus class="w-4 h-4 flex-shrink-0 mt-0.5" />
						<span>{segment.text}</span>
					</div>
				{:else if segment.type === 'added'}
					<div class="flex items-start gap-2 bg-green-100 dark:bg-green-900/30 text-success px-2 py-1 rounded">
						<Plus class="w-4 h-4 flex-shrink-0 mt-0.5" />
						<span>{segment.text}</span>
					</div>
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
