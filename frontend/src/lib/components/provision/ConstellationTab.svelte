<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Provision, type ChangeConstellationResponse } from '$lib/api';

	interface Props {
		provision: Provision;
		selectedYear: number;
	}

	let { provision, selectedYear }: Props = $props();

	let constellationData = $state<ChangeConstellationResponse | null>(null);
	let loading = $state(false);
	let error = $state('');
	let yearStart = $state(2010);
	let yearEnd = $state(2024);

	onMount(async () => {
		await loadConstellation();
	});

	async function loadConstellation() {
		loading = true;
		error = '';
		constellationData = null;

		try {
			constellationData = await api.getChangeConstellation(
				provision.provision_id,
				undefined, // section_num
				yearStart,
				yearEnd,
				undefined, // change_types
				0.0 // min_magnitude
			);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load change constellation';
			console.error('Error loading constellation:', err);
		} finally {
			loading = false;
		}
	}

	function handleRangeChange() {
		if (yearStart >= yearEnd) {
			error = 'Start year must be earlier than end year';
			return;
		}
		loadConstellation();
	}

	function viewProvision(provisionId: string, year: number) {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${year}`);
	}

	function getChangeColor(changeType: string): string {
		switch (changeType) {
			case 'added':
				return 'bg-green-500';
			case 'modified':
				return 'bg-amber-500';
			case 'removed':
				return 'bg-red-500';
			default:
				return 'bg-neutral-400';
		}
	}
</script>

<div class="space-y-6">
	<!-- Controls -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
			Change Constellation Settings
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<!-- Year range -->
			<div>
				<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
					Start Year
				</label>
				<input
					type="number"
					bind:value={yearStart}
					min="1994"
					max="2024"
					class="w-full px-4 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50"
				/>
			</div>

			<div>
				<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
					End Year
				</label>
				<input
					type="number"
					bind:value={yearEnd}
					min="1994"
					max="2024"
					class="w-full px-4 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50"
				/>
			</div>

			<div class="flex items-end">
				<button
					onclick={handleRangeChange}
					disabled={loading}
					class="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-400 text-white rounded font-medium transition-colors"
				>
					{loading ? 'Loading...' : 'Update'}
				</button>
			</div>
		</div>

		{#if error}
			<div class="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
				<p class="text-sm text-red-900 dark:text-red-100">{error}</p>
			</div>
		{/if}
	</div>

	<!-- Loading state -->
	{#if loading}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
			<div class="animate-spin w-12 h-12 mx-auto mb-4 border-4 border-blue-600 border-t-transparent rounded-full"></div>
			<p class="text-neutral-600 dark:text-neutral-400">
				Analyzing change patterns...
			</p>
		</div>
	{/if}

	<!-- Constellation data -->
	{#if !loading && constellationData}
		<!-- Overview -->
		{#if constellationData.clusters && constellationData.clusters.length > 0}
			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
				<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
					Change Clusters
				</h3>
				<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
					Groups of provisions that changed together
				</p>

				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each constellationData.clusters as cluster, idx}
						<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
							<h4 class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
								Cluster {idx + 1}
							</h4>
							{#each Object.entries(cluster) as [key, value]}
								<div class="text-xs text-neutral-600 dark:text-neutral-400">
									<span class="capitalize">{key}:</span> {value}
								</div>
							{/each}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Timeline visualization -->
		{#if constellationData.nodes && constellationData.nodes.length > 0}
			{@const nodesByYear = constellationData.nodes.reduce((acc, node) => {
				if (!acc[node.year]) acc[node.year] = [];
				acc[node.year].push(node);
				return acc;
			}, {} as Record<number, typeof constellationData.nodes>)}

			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
				<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
					Change Timeline
				</h3>

				<div class="space-y-8">
					{#each Object.entries(nodesByYear).sort(([a], [b]) => parseInt(a) - parseInt(b)) as [year, nodes]}
						<div>
							<div class="flex items-center gap-4 mb-4">
								<div class="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
									{year}
								</div>
								<div>
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
										{nodes.length} provision{nodes.length > 1 ? 's' : ''} changed
									</p>
									<div class="flex gap-2 mt-1">
										{#each ['added', 'modified', 'removed'] as type}
											{@const count = nodes.filter(n => n.change_type === type).length}
											{#if count > 0}
												<span class="text-xs px-2 py-0.5 rounded-full
													{type === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
													type === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
													'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}"
												>
													{count} {type}
												</span>
											{/if}
										{/each}
									</div>
								</div>
							</div>

							<div class="pl-20 space-y-2">
								{#each nodes as node}
									<button
										onclick={() => viewProvision(node.id, node.year)}
										class="w-full text-left p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
									>
										<div class="flex items-start gap-3">
											<div class="flex-shrink-0 pt-1">
												<div class="w-3 h-3 rounded-full {getChangeColor(node.change_type)}"></div>
											</div>

											<div class="flex-1 min-w-0">
												<div class="flex items-center gap-2 mb-1">
													<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400">
														{node.id}
													</p>
													{#if node.cluster_id !== undefined && node.cluster_id !== null}
														<span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
															Cluster {node.cluster_id}
														</span>
													{/if}
												</div>

												{#if node.heading}
													<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
														{node.heading}
													</p>
												{/if}

												<p class="text-sm text-neutral-600 dark:text-neutral-400 truncate">
													{node.label}
												</p>

												{#if node.magnitude !== undefined && node.magnitude > 0}
													<div class="mt-2 flex items-center gap-2">
														<span class="text-xs text-neutral-500 dark:text-neutral-400">
															Magnitude:
														</span>
														<div class="flex-1 max-w-xs h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
															<div
																class="h-full transition-all
																	{node.magnitude > 0.7 ? 'bg-red-500' :
																	node.magnitude > 0.3 ? 'bg-amber-500' :
																	'bg-green-500'}"
																style="width: {node.magnitude * 100}%"
															></div>
														</div>
														<span class="text-xs text-neutral-500 dark:text-neutral-400">
															{Math.round(node.magnitude * 100)}%
														</span>
													</div>
												{/if}
											</div>

											<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
											</svg>
										</div>
									</button>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
				<svg class="w-16 h-16 mx-auto text-neutral-400 dark:text-neutral-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				<p class="text-neutral-600 dark:text-neutral-400">
					No changes found in the selected year range
				</p>
				<p class="text-sm text-neutral-500 dark:text-neutral-500 mt-2">
					Try adjusting the year range to see more changes
				</p>
			</div>
		{/if}
	{/if}
</div>
