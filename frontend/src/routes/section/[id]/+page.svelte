<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Provision } from '$lib/api';
	import ProvisionCard from '$lib/components/section/ProvisionCard.svelte';
	import { auth } from '$lib/stores/auth.svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	const sectionId = $derived($page.params.id);
	let selectedYear = $state(2024);
	let provisions = $state<Provision[]>([]);
	let childCounts = $state<Map<string, number>>(new Map());
	let revisionCounts = $state<Map<string, number>>(new Map());
	let referenceCounts = $state<Map<string, number>>(new Map());
	let loading = $state(true);
	let loadingYear = $state(false);
	let error = $state('');

	const years = [1994, 2000, 2006, 2013, 2018, 2022, 2024];

	onMount(async () => {
		await loadProvisions();
	});

	function calculateChildCounts(provisions: Provision[]): Map<string, number> {
		const counts = new Map<string, number>();

		provisions.forEach((prov) => {
			const parts = prov.provision_id.split('/').filter(Boolean);

			// For each parent level, increment count
			for (let i = 3; i < parts.length - 1; i++) {
				const parentId = '/' + parts.slice(0, i + 1).join('/');
				counts.set(parentId, (counts.get(parentId) || 0) + 1);
			}
		});

		return counts;
	}

	async function loadProvisions() {
		loading = true;
		error = '';

		try {
			// Load provisions for current year
			const data = await api.getProvisions(sectionId, selectedYear);
			provisions = data.sort((a, b) => a.provision_id.localeCompare(b.provision_id));

			// Calculate child counts (frontend)
			childCounts = calculateChildCounts(provisions);

			// Fetch revision counts (backend)
			const revisions = await api.getProvisionRevisions(sectionId);
			revisionCounts = new Map(Object.entries(revisions));

			// Fetch reference counts (backend - batch)
			const provisionIds = provisions.map((p) => p.provision_id);
			const references = await api.getReferenceCounts(provisionIds, selectedYear);
			referenceCounts = new Map(Object.entries(references));
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load provisions';
		} finally {
			loading = false;
		}
	}

	async function changeYear(year: number) {
		if (loadingYear) return; // Prevent double-clicks

		loadingYear = true;
		selectedYear = year;
		try {
			await loadProvisions();
		} finally {
			loadingYear = false;
		}
	}

	function viewProvision(provision: Provision) {
		goto(`/provision/${encodeURIComponent(provision.provision_id)}?year=${selectedYear}`);
	}

	function getIndentLevel(provisionId: string): number {
		return provisionId.split('/').length - 4;
	}
</script>

<div class="flex flex-col h-full">
	<!-- Header -->
	<div
		class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-6 py-4"
	>
		<div class="max-w-6xl mx-auto">
			<button
				onclick={() => goto('/')}
				class="text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 mb-2"
			>
				← Back to Sections
			</button>

			<h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-4">
				Title 18 USC § {sectionId} - Unlawful Acts
			</h1>

			<!-- Timeline -->
			<div class="flex items-center gap-2">
				<span class="text-sm text-neutral-600 dark:text-neutral-400">Year:</span>
				<div class="flex gap-1 flex-wrap">
					{#each years as year}
						<button
							onclick={() => changeYear(year)}
							disabled={loadingYear}
							class="px-3 py-1 text-sm rounded transition-opacity {selectedYear === year
								? 'bg-blue-600 text-white'
								: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'} {loadingYear ? 'opacity-50 cursor-wait' : ''}"
						>
							{#if loadingYear && selectedYear === year}
								<span class="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin mr-1"></span>
							{/if}
							{year}
						</button>
					{/each}
				</div>
			</div>
		</div>
	</div>

	<!-- Content -->
	<div class="flex-1 overflow-y-auto bg-neutral-50 dark:bg-neutral-900">
		<div class="max-w-6xl mx-auto px-6 py-8">
			{#if loading}
				<div class="text-center py-12">
					<p class="text-neutral-500 dark:text-neutral-400">Loading provisions...</p>
				</div>
			{:else if error}
				<div
					class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
				>
					<p class="text-red-900 dark:text-red-100">{error}</p>
				</div>
			{:else if provisions.length === 0}
				<div class="text-center py-12">
					<p class="text-neutral-500 dark:text-neutral-400">
						No provisions found for this year.
					</p>
				</div>
			{:else}
				<!-- Provision cards with rich metadata -->
				<div class="provisions-grid space-y-4">
					{#each provisions as provision}
						<ProvisionCard
							{provision}
							selectedYear={selectedYear}
							childCount={childCounts.get(provision.provision_id) || 0}
							revisionCount={revisionCounts.get(provision.provision_id) || 1}
							referenceCount={referenceCounts.get(provision.provision_id) || 0}
							indentLevel={getIndentLevel(provision.provision_id)}
						/>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
