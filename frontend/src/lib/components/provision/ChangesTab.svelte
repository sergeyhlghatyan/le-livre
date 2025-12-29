<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Provision, type CompareHierarchicalResponse } from '$lib/api';
	import InlineDiff from '$lib/components/InlineDiff.svelte';

	interface Props {
		provision: Provision;
		selectedYear: number;
		initialFromYear?: number;
		initialToYear?: number;
	}

	let { provision, selectedYear, initialFromYear, initialToYear }: Props = $props();

	let compareFromYear = $state(initialFromYear ?? (selectedYear > 1994 ? selectedYear - 6 : 1994));
	let compareToYear = $state(initialToYear ?? selectedYear);
	let loading = $state(false);
	let diffData = $state<CompareHierarchicalResponse | null>(null);
	let error = $state('');

	const availableYears = [1994, 2000, 2006, 2013, 2018, 2022, 2024];

	// Derived reactive lists for dropdown options
	const validFromYears = $derived(availableYears.filter(y => y < compareToYear));
	const validToYears = $derived(availableYears.filter(y => y > compareFromYear));

	onMount(() => {
		// Auto-load diff if initial years provided
		if (initialFromYear && initialToYear) {
			loadDiff();
		}
	});

	async function loadDiff() {
		if (compareFromYear >= compareToYear) {
			error = 'From year must be earlier than to year';
			return;
		}

		loading = true;
		error = '';
		diffData = null;

		try {
			diffData = await api.compareHierarchical({
				provision_id: provision.provision_id,
				year_old: compareFromYear,
				year_new: compareToYear,
				granularity: 'sentence'
			});
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load diff';
			console.error('Error loading diff:', err);
		} finally {
			loading = false;
		}
	}

	function handleCompare() {
		loadDiff();
	}
</script>

<div class="space-y-6">
	<!-- Year selector for comparison -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
			Compare Versions
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<!-- From year -->
			<div>
				<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
					From Year
				</label>
				<select
					bind:value={compareFromYear}
					class="w-full px-4 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50"
				>
					{#each validFromYears as year}
						<option value={year}>{year}</option>
					{/each}
				</select>
			</div>

			<!-- To year -->
			<div>
				<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
					To Year
				</label>
				<select
					bind:value={compareToYear}
					class="w-full px-4 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50"
				>
					{#each validToYears as year}
						<option value={year}>{year}</option>
					{/each}
				</select>
			</div>

			<!-- Compare button -->
			<div class="flex items-end">
				<button
					onclick={handleCompare}
					disabled={loading}
					class="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-400 text-white rounded font-medium transition-colors"
				>
					{loading ? 'Loading...' : 'Compare'}
				</button>
			</div>
		</div>

		{#if error}
			<div class="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
				<p class="text-sm text-red-900 dark:text-red-100">{error}</p>
			</div>
		{/if}
	</div>

	<!-- Diff results -->
	{#if diffData && diffData.hierarchy_diff}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<div class="flex items-center justify-between mb-6">
				<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
					Changes: {compareFromYear} → {compareToYear}
				</h2>

				{#if diffData.hierarchy_diff.status}
					<span class="px-3 py-1 rounded-full text-sm font-medium
						{diffData.hierarchy_diff.status === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
						diffData.hierarchy_diff.status === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
						diffData.hierarchy_diff.status === 'removed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
						'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-400'}"
					>
						{diffData.hierarchy_diff.status}
					</span>
				{/if}
			</div>

			<!-- Diff visualization -->
			{#if diffData.hierarchy_diff.status === 'unchanged'}
				<div class="p-6 bg-neutral-50 dark:bg-neutral-900 rounded text-center">
					<svg class="w-12 h-12 mx-auto text-neutral-400 dark:text-neutral-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-neutral-600 dark:text-neutral-400">
						No changes between {compareFromYear} and {compareToYear}
					</p>
				</div>
			{:else if diffData.hierarchy_diff.status === 'added'}
				<div class="p-6 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
					<p class="text-sm text-green-900 dark:text-green-100 mb-3">
						This provision was added in {compareToYear}
					</p>
					<div class="prose dark:prose-invert max-w-none">
						<p class="text-neutral-900 dark:text-neutral-50">{diffData.hierarchy_diff.new_text}</p>
					</div>
				</div>
			{:else if diffData.hierarchy_diff.status === 'removed'}
				<div class="p-6 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
					<p class="text-sm text-red-900 dark:text-red-100 mb-3">
						This provision was removed in {compareToYear}
					</p>
					<div class="prose dark:prose-invert max-w-none">
						<p class="text-neutral-900 dark:text-neutral-50 line-through">{diffData.hierarchy_diff.old_text}</p>
					</div>
				</div>
			{:else if diffData.hierarchy_diff.inline_diff?.sentence}
				<!-- Inline diff with highlights -->
				<div class="p-6 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
					<InlineDiff parts={diffData.hierarchy_diff.inline_diff.sentence} />
				</div>
			{/if}

			<!-- Nested changes (if hierarchical) -->
			{#if diffData.hierarchy_diff.children && diffData.hierarchy_diff.children.length > 0}
				<div class="mt-6">
					<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-3">
						Changes in Child Provisions ({diffData.hierarchy_diff.children.length})
					</h3>
					<div class="space-y-2">
						{#each diffData.hierarchy_diff.children as child}
							<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">
										{child.provision_id}
									</span>
									<span class="px-2 py-0.5 rounded text-xs font-medium
										{child.status === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
										child.status === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
										child.status === 'removed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
										'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-400'}"
									>
										{child.status}
									</span>
								</div>
								{#if child.inline_diff?.sentence}
									<InlineDiff parts={child.inline_diff.sentence} />
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{:else if !loading}
		<!-- Initial state -->
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
			<svg class="w-16 h-16 mx-auto text-neutral-400 dark:text-neutral-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
			</svg>
			<p class="text-neutral-600 dark:text-neutral-400 mb-2">
				Select two years to compare changes
			</p>
			<p class="text-sm text-neutral-500 dark:text-neutral-500">
				Choose from year and to year above, then click Compare
			</p>
		</div>
	{/if}

	<!-- Loading state -->
	{#if loading}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
			<div class="animate-spin w-12 h-12 mx-auto mb-4 border-4 border-blue-600 border-t-transparent rounded-full"></div>
			<p class="text-neutral-600 dark:text-neutral-400">
				Comparing versions...
			</p>
		</div>
	{/if}
</div>
