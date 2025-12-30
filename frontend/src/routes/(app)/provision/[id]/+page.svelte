<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Provision, type ProvisionContext } from '$lib/api';
	import Tabs, { type Tab } from '$lib/components/ui/Tabs.svelte';
	import TimelineTab from '$lib/components/provision/TimelineTab.svelte';
	import RelationsTab from '$lib/components/provision/RelationsTab.svelte';
	import ChangesTab from '$lib/components/provision/ChangesTab.svelte';
	import ImpactTab from '$lib/components/provision/ImpactTab.svelte';
	import ConstellationTab from '$lib/components/provision/ConstellationTab.svelte';
	import InsightsTab from '$lib/components/provision/InsightsTab.svelte';
	import ParsedProvisionText from '$lib/components/ParsedProvisionText.svelte';
	import { auth } from '$lib/stores/auth.svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	const provisionId = $derived(decodeURIComponent($page.params.id));
	const initialYear = $derived(parseInt($page.url.searchParams.get('year') || '2024'));

	let provision = $state<Provision | null>(null);
	let context = $state<ProvisionContext | null>(null);
	let selectedYear = $state(initialYear);
	let activeTab = $state('timeline');
	let loading = $state(true);
	let loadingYear = $state(false);
	let error = $state('');
	let hasSetDefaultTab = $state(false); // Track if we've set the default tab on initial load
	let diffFromYear = $state<number | undefined>(undefined);
	let diffToYear = $state<number | undefined>(undefined);

	// Calculate tab badges from context data
	const tabs: Tab[] = $derived([
		{ id: 'overview', label: 'Overview' },
		{ id: 'timeline', label: 'Timeline' },
		{
			id: 'relations',
			label: 'Relations',
			badge: context ? (
				(context.relations?.references?.length || 0) +
				(context.relations?.referenced_by?.length || 0) +
				(context.relations?.children?.length || 0) +
				(context.relations?.parent ? 1 : 0) +
				(context.similar?.length || 0)
			) : undefined
		},
		{
			id: 'changes',
			label: 'Changes',
			badge: context?.timeline?.changes ? context.timeline.changes.filter(c => c.change_type !== 'unchanged').length : undefined
		},
		{ id: 'impact', label: 'Impact' },
		{ id: 'constellation', label: 'Constellation' },
		{ id: 'insights', label: 'Insights' }
	]);

	onMount(async () => {
		await loadProvision();
	});

	async function loadProvision() {
		loading = true;
		error = '';

		try {
			// Load main provision
			provision = await api.getProvision(provisionId, selectedYear);

			// Load rich context (includes timeline, relations, amendments, definitions, similar)
			context = await api.getProvisionContext(
				provisionId,
				selectedYear,
				true, // timeline
				true, // relations
				true, // amendments
				true, // definitions
				true  // similar
			);

			// Set smart default tab only on initial load
			if (!hasSetDefaultTab) {
				const defaultTab = selectDefaultTab();
				activeTab = defaultTab;
				hasSetDefaultTab = true;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load provision';
			console.error('Error loading provision:', err);
		} finally {
			loading = false;
		}
	}

	async function changeYear(year: number) {
		if (loadingYear) return; // Prevent double-clicks

		loadingYear = true;
		selectedYear = year;
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${year}`, { replaceState: true });
		try {
			await loadProvision();
		} finally {
			loadingYear = false;
		}
	}

	function goBack() {
		if (provision) {
			goto(`/section/${provision.section_num}`);
		} else {
			goto('/');
		}
	}

	function handleTabChange(tabId: string) {
		activeTab = tabId;
	}

	function handleViewDiff(fromYear: number, toYear: number) {
		// Store years for pre-loading in Changes tab
		diffFromYear = fromYear;
		diffToYear = toYear;
		activeTab = 'changes';
	}

	function viewProvision(provisionId: string) {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${selectedYear}`);
	}

	function viewAllRelations() {
		activeTab = 'relations';
	}

	// Smart default tab selection based on provision data
	function selectDefaultTab() {
		// Always default to Overview tab on first load
		return 'overview';
	}

	// Calculate importance score (from InsightsTab logic)
	function calculateImportanceScore(): number {
		if (!context) return 50;
		let score = 50;
		if (context.relations?.referenced_by) {
			score += Math.min(context.relations.referenced_by.length * 5, 30);
		}
		if (context.relations?.children) {
			score += Math.min(context.relations.children.length * 2, 15);
		}
		if (context.amendments && context.amendments.length > 0) {
			score += Math.min(context.amendments.length * 3, 10);
		}
		return Math.min(score, 100);
	}

	// Get last modified years from timeline
	function getLastModifiedYears(): number[] {
		if (!context?.timeline?.changes) return [];
		return context.timeline.changes
			.filter(c => c.change_type === 'modified' || c.change_type === 'added')
			.map(c => c.year)
			.sort((a, b) => b - a)
			.slice(0, 3);
	}

	// Get change status for current year
	function getChangeStatus(): { type: string; label: string; color: string } {
		if (!context?.timeline?.changes) return { type: 'unknown', label: 'Unknown', color: 'bg-neutral-400' };

		const recentChanges = context.timeline.changes.filter(c => c.year >= selectedYear - 10);
		if (recentChanges.length === 0) return { type: 'stable', label: 'Stable', color: 'bg-green-500' };

		const hasModified = recentChanges.some(c => c.change_type === 'modified');
		const hasAdded = recentChanges.some(c => c.change_type === 'added');
		const hasRemoved = recentChanges.some(c => c.change_type === 'removed');

		if (hasRemoved) return { type: 'removed', label: 'Removed', color: 'bg-red-500' };
		if (hasAdded) return { type: 'added', label: 'Recently Added', color: 'bg-blue-500' };
		if (hasModified) return { type: 'modified', label: 'Modified', color: 'bg-amber-500' };

		return { type: 'stable', label: 'Stable', color: 'bg-green-500' };
	}
</script>

<div class="flex flex-col h-full bg-neutral-50 dark:bg-neutral-900">
	<!-- Header with provision text (always visible) -->
	<div class="flex-shrink-0 bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800">
		<div class="max-w-6xl mx-auto px-6 py-6">
			<!-- Back button -->
			<button
				onclick={goBack}
				class="text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 mb-4 flex items-center gap-2"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
				Back to Section
			</button>

			{#if loading}
				<div class="py-8">
					<p class="text-neutral-500 dark:text-neutral-400">Loading provision...</p>
				</div>
			{:else if error}
				<div class="py-8">
					<div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
						<p class="text-red-900 dark:text-red-100">{error}</p>
					</div>
				</div>
			{:else if provision}
				<!-- Provision header -->
				<div class="mb-6">
					<h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-2">
						{provision.heading || provision.provision_id}
					</h1>
					<div class="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
						<span class="font-mono">{provisionId}</span>
						<span>•</span>
						<span>{selectedYear}</span>
						{#if provision.provision_level}
							<span>•</span>
							<span class="capitalize">{provision.provision_level}</span>
						{/if}
					</div>

					<!-- Metadata Section -->
					{#if context}
						{@const changeStatus = getChangeStatus()}
						{@const modifiedYears = getLastModifiedYears()}
						{@const importanceScore = calculateImportanceScore()}

						<div class="mt-4 flex flex-wrap gap-3">
							<!-- Change status badge -->
							<div class="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
								<div class="w-2 h-2 rounded-full {changeStatus.color}"></div>
								<span class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
									{changeStatus.label}
								</span>
								{#if modifiedYears.length > 0}
									<span class="text-xs text-neutral-500 dark:text-neutral-400">
										({modifiedYears.join(', ')})
									</span>
								{/if}
							</div>

							<!-- Importance score -->
							<div class="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
								<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
								</svg>
								<span class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
									Importance: {importanceScore}/100
								</span>
							</div>

							<!-- Reference counts -->
							{#if context.relations}
								{@const refCount = context.relations.references?.length || 0}
								{@const refByCount = context.relations.referenced_by?.length || 0}
								{@const childCount = context.relations.children?.length || 0}

								{#if refCount > 0 || refByCount > 0}
									<div class="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
										<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
										</svg>
										<span class="text-sm text-neutral-900 dark:text-neutral-50">
											{refCount} refs • {refByCount} cited by
										</span>
									</div>
								{/if}

								{#if childCount > 0}
									<div class="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
										<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
										</svg>
										<span class="text-sm text-neutral-900 dark:text-neutral-50">
											{childCount} child provision{childCount !== 1 ? 's' : ''}
										</span>
									</div>
								{/if}
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Tab navigation -->
		{#if !loading && !error && provision}
			<div class="max-w-6xl mx-auto px-6">
				<Tabs {tabs} {activeTab} onTabChange={handleTabChange} />
			</div>
		{/if}
	</div>

	<!-- Tab content -->
	<div class="flex-1 overflow-y-auto">
		<div class="max-w-6xl mx-auto px-6 py-8">
			{#if !loading && !error && provision && context}
				{#if activeTab === 'overview'}
					<div class="space-y-6">
						<!-- Provision text with clickable cross-references -->
						<div class="prose dark:prose-invert max-w-none">
							<div class="p-6 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
								<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
									Provision Text
								</h2>
								<ParsedProvisionText
									text={provision.text_content}
									currentSection={provision.section_num}
									currentYear={selectedYear}
									currentProvisionHeading={provision.heading || provision.provision_id}
									class="text-neutral-900 dark:text-neutral-50 whitespace-pre-wrap leading-relaxed"
								/>
							</div>
						</div>

						<!-- Quick Links Section -->
						{#if context.relations && (context.relations.parent || context.relations.children?.length > 0 || context.relations.references?.length > 0)}
							<div class="p-6 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
								<div class="flex items-center justify-between mb-6">
									<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
										Quick Links
									</h2>
									<button
										onclick={viewAllRelations}
										class="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
									>
										View all in Relations
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										</svg>
									</button>
								</div>

								<div class="space-y-4">
									<!-- Parent -->
									{#if context.relations.parent}
										<div>
											<div class="flex items-center gap-2 mb-3">
												<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
												</svg>
												<span class="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Parent</span>
											</div>
											<button
												onclick={() => viewProvision(context.relations.parent.provision_id)}
												class="w-full text-left px-4 py-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
											>
												<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-1">
													{context.relations.parent.provision_id}
												</p>
												{#if context.relations.parent.heading}
													<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
														{context.relations.parent.heading}
													</p>
												{/if}
											</button>
										</div>
									{/if}

									<!-- Children -->
									{#if context.relations.children && context.relations.children.length > 0}
										<div>
											<div class="flex items-center gap-2 mb-3">
												<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
												</svg>
												<span class="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
													Children ({context.relations.children.length})
												</span>
											</div>
											<div class="space-y-2">
												{#each context.relations.children.slice(0, 5) as child}
													<button
														onclick={() => viewProvision(child.provision_id)}
														class="w-full text-left px-4 py-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
													>
														<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-1">
															{child.provision_id}
														</p>
														{#if child.heading}
															<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
																{child.heading}
															</p>
														{/if}
													</button>
												{/each}
												{#if context.relations.children.length > 5}
													<button
														onclick={viewAllRelations}
														class="w-full text-center px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
													>
														+{context.relations.children.length - 5} more children
													</button>
												{/if}
											</div>
										</div>
									{/if}

									<!-- References -->
									{#if context.relations.references && context.relations.references.length > 0}
										<div>
											<div class="flex items-center gap-2 mb-3">
												<svg class="w-4 h-4 text-neutral-600 dark:text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
												</svg>
												<span class="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
													References ({context.relations.references.length})
												</span>
											</div>
											<div class="space-y-2">
												{#each context.relations.references.slice(0, 5) as ref}
													<button
														onclick={() => viewProvision(ref.provision_id)}
														class="w-full text-left px-4 py-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
													>
														<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-1">
															{ref.provision_id}
														</p>
														{#if ref.heading}
															<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
																{ref.heading}
															</p>
														{/if}
													</button>
												{/each}
												{#if context.relations.references.length > 5}
													<button
														onclick={viewAllRelations}
														class="w-full text-center px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
													>
														+{context.relations.references.length - 5} more references
													</button>
												{/if}
											</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				{:else if activeTab === 'timeline'}
					<TimelineTab
						{provision}
						{context}
						{selectedYear}
						{loadingYear}
						onYearChange={changeYear}
						onViewDiff={handleViewDiff}
					/>
				{:else if activeTab === 'relations'}
					<RelationsTab
						{provision}
						{context}
						{selectedYear}
					/>
				{:else if activeTab === 'changes'}
					<ChangesTab
						{provision}
						{selectedYear}
						initialFromYear={diffFromYear}
						initialToYear={diffToYear}
					/>
				{:else if activeTab === 'impact'}
					<ImpactTab
						{provision}
						{selectedYear}
					/>
				{:else if activeTab === 'constellation'}
					<ConstellationTab
						{provision}
						{selectedYear}
					/>
				{:else if activeTab === 'insights'}
					<InsightsTab
						{provision}
						{context}
					/>
				{/if}
			{/if}
		</div>
	</div>
</div>
