<script lang="ts">
	import { api, type CompareHierarchicalResponse, type HierarchyNode } from '$lib/api';
	import HierarchyTree from '$lib/components/HierarchyTree.svelte';

	let provisionId = $state('/us/usc/t18/s922/a');
	let yearOld = $state(1994);
	let yearNew = $state(2024);
	let granularity = $state<'word' | 'sentence'>('sentence');
	let loading = $state(false);
	let result = $state<CompareHierarchicalResponse | null>(null);
	let error = $state('');

	// Calculate change statistics
	const changeStats = $derived.by(() => {
		if (!result) return null;

		let modified = 0;
		let added = 0;
		let removed = 0;
		let unchanged = 0;

		function countChanges(node: HierarchyNode) {
			switch (node.status) {
				case 'modified':
					modified++;
					break;
				case 'added':
					added++;
					break;
				case 'removed':
					removed++;
					break;
				case 'unchanged':
					unchanged++;
					break;
			}
			node.children.forEach(countChanges);
		}

		countChanges(result.hierarchy_diff);

		return { modified, added, removed, unchanged, total: modified + added + removed + unchanged };
	});

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
		} catch (err) {
			error = err instanceof Error ? err.message : 'Comparison failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="px-4 py-6 max-w-7xl mx-auto">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-2">Hierarchical Compare</h1>
		<p class="text-gray-600">
			Compare provisions at all levels: subsections, paragraphs, clauses, and subclauses
		</p>
	</div>

	<!-- Compare Form -->
	<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleCompare();
			}}
		>
			<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
				<div class="md:col-span-2">
					<label for="provision" class="block text-sm font-medium text-gray-700 mb-2">
						Provision ID
					</label>
					<input
						id="provision"
						type="text"
						bind:value={provisionId}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
						placeholder="/us/usc/t18/s922/a"
					/>
				</div>
				<div>
					<label for="year-old" class="block text-sm font-medium text-gray-700 mb-2">
						From Year
					</label>
					<input
						id="year-old"
						type="number"
						bind:value={yearOld}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>
				<div>
					<label for="year-new" class="block text-sm font-medium text-gray-700 mb-2">
						To Year
					</label>
					<input
						id="year-new"
						type="number"
						bind:value={yearNew}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>
			</div>

			<!-- Granularity Toggle -->
			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-2">Diff Granularity</label>
				<div class="flex gap-4">
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="radio"
							bind:group={granularity}
							value="sentence"
							class="text-blue-600 focus:ring-blue-500"
						/>
						<span class="text-sm">Sentence-level</span>
					</label>
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="radio"
							bind:group={granularity}
							value="word"
							class="text-blue-600 focus:ring-blue-500"
						/>
						<span class="text-sm">Word-level</span>
					</label>
				</div>
			</div>

			<button
				type="submit"
				disabled={loading || !provisionId.trim()}
				class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
			>
				{loading ? 'Comparing...' : 'Compare Versions'}
			</button>
		</form>
	</div>

	<!-- Error Message -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
			<p class="text-red-800">{error}</p>
		</div>
	{/if}

	<!-- Results -->
	{#if result}
		<div class="space-y-6">
			<!-- AI Summary -->
			<div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
				<h2 class="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
					<span class="text-2xl">🤖</span>
					AI Summary
				</h2>
				<div class="prose max-w-none text-gray-700 whitespace-pre-wrap">
					{result.summary}
				</div>
			</div>

			<!-- Change Statistics -->
			{#if changeStats}
				<div class="bg-white border border-gray-200 rounded-lg p-6">
					<h2 class="text-lg font-semibold text-gray-900 mb-4">Change Statistics</h2>
					<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
						<div class="text-center">
							<div class="text-2xl font-bold text-red-600">{changeStats.modified}</div>
							<div class="text-sm text-gray-600">Modified</div>
						</div>
						<div class="text-center">
							<div class="text-2xl font-bold text-green-600">{changeStats.added}</div>
							<div class="text-sm text-gray-600">Added</div>
						</div>
						<div class="text-center">
							<div class="text-2xl font-bold text-gray-600">{changeStats.removed}</div>
							<div class="text-sm text-gray-600">Removed</div>
						</div>
						<div class="text-center">
							<div class="text-2xl font-bold text-gray-400">{changeStats.unchanged}</div>
							<div class="text-sm text-gray-600">Unchanged</div>
						</div>
						<div class="text-center">
							<div class="text-2xl font-bold text-blue-600">{changeStats.total}</div>
							<div class="text-sm text-gray-600">Total Provisions</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Hierarchical Tree View -->
			<div class="bg-white border border-gray-200 rounded-lg p-6">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-lg font-semibold text-gray-900">Hierarchical Changes</h2>
					<div class="text-sm text-gray-600">
						Comparing {result.year_old} → {result.year_new}
					</div>
				</div>

				<!-- Legend -->
				<div class="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
					<div class="flex items-center gap-2">
						<span>🔴</span>
						<span class="text-sm text-gray-700">Modified</span>
					</div>
					<div class="flex items-center gap-2">
						<span>➕</span>
						<span class="text-sm text-gray-700">Added</span>
					</div>
					<div class="flex items-center gap-2">
						<span>➖</span>
						<span class="text-sm text-gray-700">Removed</span>
					</div>
					<div class="flex items-center gap-2">
						<span>✅</span>
						<span class="text-sm text-gray-700">Unchanged</span>
					</div>
				</div>

				<!-- Tree -->
				<div class="hierarchy-container">
					<HierarchyTree node={result.hierarchy_diff} bind:granularity />
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.hierarchy-container {
		max-height: 100vh;
		overflow-y: auto;
	}
</style>
