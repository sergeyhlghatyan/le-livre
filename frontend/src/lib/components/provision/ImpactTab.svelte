<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Provision, type ImpactRadiusResponse } from '$lib/api';

	interface Props {
		provision: Provision;
		selectedYear: number;
	}

	let { provision, selectedYear }: Props = $props();

	let impactData = $state<ImpactRadiusResponse | null>(null);
	let loading = $state(false);
	let error = $state('');
	let depth = $state(2);

	onMount(async () => {
		await loadImpactRadius();
	});

	async function loadImpactRadius() {
		loading = true;
		error = '';
		impactData = null;

		try {
			impactData = await api.getImpactRadius(
				provision.provision_id,
				selectedYear,
				depth,
				true, // include_hierarchical
				true, // include_references
				false // include_amendments
			);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load impact radius';
			console.error('Error loading impact radius:', err);
		} finally {
			loading = false;
		}
	}

	function handleDepthChange(newDepth: number) {
		depth = newDepth;
		loadImpactRadius();
	}

	function viewProvision(provisionId: string) {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${selectedYear}`);
	}

	function getDistanceLabel(distance: number): string {
		if (distance === 0) return 'Center';
		if (distance === 1) return 'Direct';
		if (distance === 2) return 'Secondary';
		return `Level ${distance}`;
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
		<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
			Impact Radius Settings
		</h2>

		<div class="flex items-center gap-6">
			<div class="flex-1">
				<label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
					Depth (relationship hops)
				</label>
				<div class="flex gap-2">
					{#each [1, 2, 3] as d}
						<button
							onclick={() => handleDepthChange(d)}
							class="px-4 py-2 rounded text-sm font-medium transition-colors
								{depth === d
									? 'bg-blue-600 text-white'
									: 'bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-600'}"
						>
							{d} hop{d > 1 ? 's' : ''}
						</button>
					{/each}
				</div>
			</div>

			{#if impactData?.stats}
				<div class="flex-shrink-0 p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
					<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-1">Total Provisions</p>
					<p class="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
						{impactData.stats.total || 0}
					</p>
				</div>
			{/if}
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
				Computing impact radius...
			</p>
		</div>
	{/if}

	<!-- Impact data -->
	{#if !loading && impactData}
		<!-- Statistics -->
		{#if impactData.stats}
			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
				<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
					Impact Statistics
				</h3>

				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					{#each Object.entries(impactData.stats) as [key, value]}
						<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
							<p class="text-xs text-neutral-600 dark:text-neutral-400 mb-1 capitalize">
								{key.replace('_', ' ')}
							</p>
							<p class="text-xl font-bold text-neutral-900 dark:text-neutral-50">
								{value}
							</p>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Affected provisions by distance -->
		{#if impactData.nodes && impactData.nodes.length > 0}
			{@const nodesByDistance = impactData.nodes.reduce((acc, node) => {
				const dist = node.distance || 0;
				if (!acc[dist]) acc[dist] = [];
				acc[dist].push(node);
				return acc;
			}, {} as Record<number, typeof impactData.nodes>)}

			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
				<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
					Affected Provisions
				</h3>

				<div class="space-y-6">
					{#each Object.entries(nodesByDistance).sort(([a], [b]) => parseInt(a) - parseInt(b)) as [distance, nodes]}
						<div>
							<h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
								{getDistanceLabel(parseInt(distance))} ({nodes.length})
							</h4>

							<div class="space-y-2">
								{#each nodes as node}
									<button
										onclick={() => viewProvision(node.id)}
										class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
									>
										<div class="flex items-start gap-3">
											<!-- Change indicator -->
											<div class="flex-shrink-0 pt-1">
												<div class="w-3 h-3 rounded-full {getChangeColor(node.change_type)}"></div>
											</div>

											<!-- Provision info -->
											<div class="flex-1 min-w-0">
												<div class="flex items-center gap-2 mb-1">
													<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400">
														{node.id}
													</p>
													{#if node.change_type !== 'unchanged'}
														<span class="px-2 py-0.5 text-xs rounded-full
															{node.change_type === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
															node.change_type === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
															'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}"
														>
															{node.change_type}
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

												<!-- Change magnitude -->
												{#if node.magnitude !== undefined && node.magnitude > 0}
													<div class="mt-2 flex items-center gap-2">
														<span class="text-xs text-neutral-500 dark:text-neutral-400">
															Impact:
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
		{/if}

		<!-- Empty state -->
		{#if !impactData.nodes || impactData.nodes.length === 0}
			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
				<svg class="w-16 h-16 mx-auto text-neutral-400 dark:text-neutral-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
				</svg>
				<p class="text-neutral-600 dark:text-neutral-400">
					No related provisions found within {depth} hop{depth > 1 ? 's' : ''}
				</p>
			</div>
		{/if}
	{/if}
</div>
