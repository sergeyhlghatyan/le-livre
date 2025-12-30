<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type ProvisionContext } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import { auth } from '$lib/stores/auth.svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	const provisionId = $derived(decodeURIComponent($page.params.id));
	const year = $derived(parseInt($page.url.searchParams.get('year') || '2024'));

	let loading = $state(true);
	let error = $state('');
	let activeTab = $state<'text' | 'graph' | 'timeline' | 'similar'>('text');

	// Data to load
	let context = $state<ProvisionContext | null>(null);
	let compareYearOld = $state(2018);
	let compareYearNew = $state(2024);
	let comparisonData = $state<any>(null);

	onMount(async () => {
		await loadProvisionDetails();
	});

	async function loadProvisionDetails() {
		loading = true;
		error = '';
		try {
			// Load provision context
			context = await api.getProvisionContext(provisionId, year);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load provision details';
		} finally {
			loading = false;
		}
	}

	async function loadComparison() {
		try {
			comparisonData = await api.compareHierarchical({
				provision_id: provisionId,
				year_old: compareYearOld,
				year_new: compareYearNew,
				granularity: 'word'
			});
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load comparison';
		}
	}
</script>

<div class="flex flex-col h-full bg-neutral-50 dark:bg-neutral-900">
	<!-- Header -->
	<header class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-6 py-4">
		<div class="max-w-6xl mx-auto">
			<button
				onclick={() => history.back()}
				class="text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 mb-2"
			>
				← Back
			</button>

			{#if context}
				<h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-1">
					{context.provision.provision_num}
					{#if context.provision.heading}
						- {context.provision.heading}
					{/if}
				</h1>
				<div class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
					<span>Year: {year}</span>
					<span>•</span>
					<span>Level: {context.provision.provision_level}</span>
				</div>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="flex-1 flex items-center justify-center">
			<p class="text-neutral-500 dark:text-neutral-400">Loading provision details...</p>
		</div>
	{:else if error}
		<div class="flex-1 flex items-center justify-center">
			<div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
				<p class="text-red-900 dark:text-red-100">{error}</p>
			</div>
		</div>
	{:else if context}
		<!-- Tab Navigation -->
		<div class="flex-shrink-0 bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800">
			<div class="max-w-6xl mx-auto px-6">
				<div class="flex gap-1">
					<button
						onclick={() => activeTab = 'text'}
						class="px-4 py-3 text-sm font-medium transition-colors {activeTab === 'text'
							? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
							: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'}"
					>
						Full Text
					</button>
					<button
						onclick={() => activeTab = 'graph'}
						class="px-4 py-3 text-sm font-medium transition-colors {activeTab === 'graph'
							? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
							: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'}"
					>
						Graph Visualization
					</button>
					<button
						onclick={() => activeTab = 'timeline'}
						class="px-4 py-3 text-sm font-medium transition-colors {activeTab === 'timeline'
							? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
							: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'}"
					>
						Timeline & Revisions
					</button>
					<button
						onclick={() => activeTab = 'similar'}
						class="px-4 py-3 text-sm font-medium transition-colors {activeTab === 'similar'
							? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
							: 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'}"
					>
						Similar Provisions
					</button>
				</div>
			</div>
		</div>

		<!-- Tab Content -->
		<div class="flex-1 overflow-y-auto">
			<div class="max-w-6xl mx-auto px-6 py-8">
				{#if activeTab === 'text'}
					<section class="space-y-6">
						<!-- Full provision text -->
						<div class="bg-white dark:bg-neutral-800 rounded-lg p-6 border border-neutral-200 dark:border-neutral-700">
							<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
								Complete Provision Text
							</h2>
							<p class="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap font-mono">
								{context.provision.text_content}
							</p>
						</div>

						<!-- Relationships -->
						{#if context.relations}
							<div class="bg-white dark:bg-neutral-800 rounded-lg p-6 border border-neutral-200 dark:border-neutral-700">
								<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
									Relationships
								</h2>

								{#if context.relations.parent}
									<div class="mb-4">
										<h3 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
											Parent Provision
										</h3>
										<div class="p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
											<p class="text-sm font-mono">{context.relations.parent.provision_id}</p>
											{#if context.relations.parent.heading}
												<p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
													{context.relations.parent.heading}
												</p>
											{/if}
										</div>
									</div>
								{/if}

								{#if context.relations.children.length > 0}
									<div class="mb-4">
										<h3 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
											Child Provisions ({context.relations.children.length})
										</h3>
										<div class="space-y-2">
											{#each context.relations.children as child}
												<div class="p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
													<p class="text-sm font-mono">{child.provision_id}</p>
													{#if child.heading}
														<p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
															{child.heading}
														</p>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								{#if context.relations.references.length > 0}
									<div class="mb-4">
										<h3 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
											References ({context.relations.references.length})
										</h3>
										<div class="space-y-2">
											{#each context.relations.references as ref}
												<div class="p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
													<p class="text-sm font-mono">{ref.provision_id}</p>
													{#if ref.heading}
														<p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
															{ref.heading}
														</p>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								{#if context.relations.referenced_by.length > 0}
									<div>
										<h3 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
											Referenced By ({context.relations.referenced_by.length})
										</h3>
										<div class="space-y-2">
											{#each context.relations.referenced_by as ref}
												<div class="p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
													<p class="text-sm font-mono">{ref.provision_id}</p>
													{#if ref.heading}
														<p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
															{ref.heading}
														</p>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/if}
					</section>
				{/if}

				{#if activeTab === 'graph'}
					<section>
						<div class="bg-white dark:bg-neutral-800 rounded-lg p-6 border border-neutral-200 dark:border-neutral-700">
							<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
								Provision Relationship Graph
							</h2>
							<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
								View an interactive graph visualization showing relationships between provisions.
							</p>
							<Button
								variant="primary"
								onclick={() => goto(`/graph?provision=${encodeURIComponent(provisionId)}&year=${year}`)}
							>
								Open Graph Visualization
							</Button>
						</div>
					</section>
				{/if}

				{#if activeTab === 'timeline'}
					<section class="space-y-6">
						<div class="bg-white dark:bg-neutral-800 rounded-lg p-6 border border-neutral-200 dark:border-neutral-700">
							<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
								Revision History
							</h2>
							<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
								This provision exists in {context.timeline.length} different years:
							</p>

							<div class="flex gap-2 flex-wrap mb-6">
								{#each context.timeline as timelineYear}
									<a
										href="/response-detail/{encodeURIComponent(provisionId)}?year={timelineYear}"
										class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors {timelineYear === year
											? 'bg-blue-600 text-white'
											: 'bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-600'}"
									>
										{timelineYear}
									</a>
								{/each}
							</div>

							<!-- Compare versions -->
							<h3 class="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
								Compare Versions
							</h3>
							<div class="flex items-center gap-3 mb-4">
								<select
									bind:value={compareYearOld}
									class="px-3 py-2 rounded-md border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 text-sm"
								>
									{#each context.timeline as y}
										<option value={y}>{y}</option>
									{/each}
								</select>
								<span class="text-neutral-600 dark:text-neutral-400">vs</span>
								<select
									bind:value={compareYearNew}
									class="px-3 py-2 rounded-md border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 text-sm"
								>
									{#each context.timeline as y}
										<option value={y}>{y}</option>
									{/each}
								</select>
								<button
									onclick={loadComparison}
									class="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
								>
									Compare
								</button>
							</div>

							{#if comparisonData}
								<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
									<p class="text-sm text-neutral-700 dark:text-neutral-300">
										Comparison data loaded. (Diff viewer component not yet implemented)
									</p>
								</div>
							{/if}
						</div>
					</section>
				{/if}

				{#if activeTab === 'similar'}
					<section>
						<div class="bg-white dark:bg-neutral-800 rounded-lg p-6 border border-neutral-200 dark:border-neutral-700">
							<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
								Semantically Similar Provisions
							</h2>
							<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
								Provisions with similar content based on semantic analysis:
							</p>

							{#if context.similar && context.similar.length > 0}
								<div class="space-y-3">
									{#each context.similar as item}
										<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
											<div class="flex items-center justify-between mb-2">
												<p class="text-sm font-mono font-semibold text-neutral-900 dark:text-neutral-100">
													{item.provision.provision_id}
												</p>
												<span class="text-xs px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium">
													{(item.similarity_score * 100).toFixed(1)}% similar
												</span>
											</div>
											{#if item.provision.heading}
												<p class="text-sm text-neutral-700 dark:text-neutral-300 mb-1">
													{item.provision.heading}
												</p>
											{/if}
											<p class="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">
												{item.provision.text_content.substring(0, 150)}...
											</p>
										</div>
									{/each}
								</div>
							{:else}
								<p class="text-sm text-neutral-500">No similar provisions found.</p>
							{/if}
						</div>
					</section>
				{/if}
			</div>
		</div>
	{/if}
</div>
