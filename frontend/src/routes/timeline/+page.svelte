<script lang="ts">
	import { api, type Provision, type TimelineChange } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Breadcrumb, { type BreadcrumbItem } from '$lib/components/ui/Breadcrumb.svelte';
	import { prefetch } from '$lib/actions/prefetch';
	import { auth } from '$lib/stores/auth.svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	let section = $state('922');
	let years = $state<number[]>([]);
	let selectedYear = $state<number | null>(null);
	let provisions = $state<Provision[]>([]);
	let loading = $state(false);
	let error = $state('');
	let expanded = $state(false);
	let provisionChanges = $state<Map<string, TimelineChange[]>>(new Map());

	const breadcrumbItems = $derived<BreadcrumbItem[]>([
		{ label: 'Home', href: '/' },
		{ label: 'Timeline', href: undefined },
		...(years.length > 0 ? [{ label: `§ ${section}` }] : [])
	]);

	onMount(async () => {
		await loadTimeline();
	});

	async function loadTimeline() {
		loading = true;
		error = '';
		provisions = [];
		selectedYear = null;

		try {
			const timeline = await api.getTimeline(section);
			years = timeline.years;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load timeline';
		} finally {
			loading = false;
		}
	}

	async function selectYear(year: number) {
		selectedYear = year;
		expanded = true;
		loading = true;
		error = '';

		try {
			provisions = await api.getProvisions(section, year);

			// Fetch timeline changes for each provision
			for (const provision of provisions) {
				if (!provisionChanges.has(provision.provision_id)) {
					try {
						const changes = await api.getProvisionTimelineChanges(provision.provision_id);
						provisionChanges.set(provision.provision_id, changes);
						provisionChanges = new Map(provisionChanges); // Trigger reactivity
					} catch (err) {
						console.warn(`Failed to load changes for ${provision.provision_id}:`, err);
					}
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load provisions';
		} finally {
			loading = false;
		}
	}

	function compareWithPrevious() {
		if (!selectedYear || years.length === 0) return;
		const currentIndex = years.indexOf(selectedYear);
		if (currentIndex > 0) {
			const prevYear = years[currentIndex - 1];
			goto(`/compare?provision=/us/usc/t18/s${section}/a&from=${prevYear}&to=${selectedYear}`);
		}
	}

	function navigateToProvision(provision: Provision, e: MouseEvent) {
		e.preventDefault();
		goto(`/provision/${encodeURIComponent(provision.provision_id)}?year=${provision.year}`);
	}

	function viewInGraph(provision: Provision, e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		goto(`/graph?provision=${encodeURIComponent(provision.provision_id)}&year=${provision.year}`);
	}

	function compareVersions(provision: Provision, e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		goto(`/compare?provision=${encodeURIComponent(provision.provision_id)}&from=1994&to=${provision.year}`);
	}

	/**
	 * Get aggregate change info for a year across all provisions
	 */
	function getYearChangeInfo(year: number): { type: string; magnitude: number } {
		let totalMagnitude = 0;
		let changeTypes = new Set<string>();
		let count = 0;

		for (const changes of provisionChanges.values()) {
			const yearChange = changes.find((c) => c.year === year);
			if (yearChange) {
				totalMagnitude += yearChange.magnitude || 0;
				changeTypes.add(yearChange.change_type);
				count++;
			}
		}

		const avgMagnitude = count > 0 ? totalMagnitude / count : 0;

		// Determine primary change type
		let primaryType = 'unchanged';
		if (changeTypes.has('added')) primaryType = 'added';
		else if (changeTypes.has('modified')) primaryType = 'modified';
		else if (changeTypes.has('removed')) primaryType = 'removed';

		return { type: primaryType, magnitude: avgMagnitude };
	}

	/**
	 * Get marker size class based on magnitude
	 */
	function getMarkerSize(magnitude: number): string {
		if (magnitude === 0) return 'w-2 h-2';
		if (magnitude < 0.3) return 'w-2.5 h-2.5';
		if (magnitude < 0.7) return 'w-3 h-3';
		return 'w-4 h-4';
	}

	/**
	 * Get marker color class based on change type
	 */
	function getMarkerColor(changeType: string, isSelected: boolean): string {
		if (isSelected) return 'bg-primary';

		switch (changeType) {
			case 'added':
				return 'bg-green-500 dark:bg-green-600';
			case 'modified':
				return 'bg-yellow-500 dark:bg-yellow-600';
			case 'removed':
				return 'bg-red-500 dark:bg-red-600';
			default:
				return 'bg-neutral-400 dark:bg-neutral-600';
		}
	}

	/**
	 * Get tooltip text for year marker
	 */
	function getYearTooltip(year: number): string {
		const info = getYearChangeInfo(year);
		if (info.magnitude === 0) return `${year}: No changes`;

		const magnitudeText =
			info.magnitude < 0.3 ? 'Minor changes' : info.magnitude < 0.7 ? 'Moderate changes' : 'Major changes';

		return `${year}: ${info.type} (${magnitudeText})`;
	}
</script>

<div class="flex flex-col h-full">
	<!-- Header -->
	<div class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-6 py-3">
		<Breadcrumb items={breadcrumbItems} />
		<h1 class="text-lg font-medium text-neutral-900 dark:text-neutral-50 mt-3">
			{#if years.length > 0}
				Timeline: § {section}
			{:else}
				Timeline
			{/if}
		</h1>
	</div>

	{#if years.length === 0}
		<!-- Section Input -->
		<div class="flex-1 overflow-y-auto px-6 py-8">
			<div class="max-w-2xl mx-auto">
				<form
					onsubmit={(e) => {
						e.preventDefault();
						loadTimeline();
					}}
					class="space-y-4"
				>
					<div>
						<label class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
							Section
						</label>
						<Input bind:value={section} placeholder="922" />
					</div>

					<Button type="submit" variant="primary" disabled={loading || !section.trim()}>
						{loading ? 'Loading...' : 'Load Timeline'}
					</Button>
				</form>

				{#if error}
					<div class="mt-6 p-4 border border-error rounded-lg bg-white dark:bg-neutral-950 text-error text-sm">
						{error}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<!-- Timeline View -->
		<div class="flex-1 overflow-y-auto px-6 py-8">
			<div class="max-w-4xl mx-auto">
				<!-- Horizontal Timeline -->
				<div class="mb-12">
					<div class="relative">
						<!-- Timeline Line -->
						<div class="absolute top-1/2 left-0 right-0 h-px bg-neutral-300 dark:bg-neutral-700 -translate-y-1/2"></div>

						<!-- Year Markers -->
						<div class="relative flex justify-between items-center">
							{#each years as year}
								{@const changeInfo = getYearChangeInfo(year)}
								{@const isSelected = selectedYear === year}
								<button
									onclick={() => selectYear(year)}
									class="relative flex flex-col items-center gap-2 group"
									title={getYearTooltip(year)}
								>
									<!-- Dot with dynamic size and color -->
									<div
										class="{getMarkerSize(changeInfo.magnitude)} {getMarkerColor(
											changeInfo.type,
											isSelected
										)} rounded-full transition-all {isSelected
											? 'scale-125'
											: 'group-hover:scale-110'}"
									></div>

									<!-- Year Label -->
									<span
										class="text-xs font-mono transition-colors {isSelected
											? 'text-primary font-medium'
											: 'text-neutral-500 dark:text-neutral-400 group-hover:text-neutral-900 dark:group-hover:text-neutral-50'}"
									>
										{year}
									</span>
								</button>
							{/each}
						</div>
					</div>
				</div>

				<!-- Selected Year Details -->
				{#if selectedYear}
					<div class="border border-neutral-200 dark:border-neutral-800 rounded-lg bg-white dark:bg-neutral-950 p-6">
						<div class="flex items-center justify-between mb-4">
							<div>
								<h2 class="text-base font-medium text-neutral-900 dark:text-neutral-50">
									{selectedYear}
								</h2>
								<p class="text-xs text-neutral-500 dark:text-neutral-400">
									{provisions.length} provisions
								</p>
							</div>

							<div class="flex items-center gap-2">
								<Button variant="ghost" onclick={compareWithPrevious}>
									Compare with Previous
								</Button>
								<Button
									variant="ghost"
									onclick={() =>
										goto(`/compare?provision=/us/usc/t18/s${section}/a&from=${selectedYear}&to=${years[years.length - 1]}`)}
								>
									View Full Text
								</Button>
							</div>
						</div>

						{#if loading}
							<div class="text-sm text-neutral-500 dark:text-neutral-400">Loading...</div>
						{:else if provisions.length > 0}
							<div class="space-y-3">
								{#each provisions.slice(0, expanded ? undefined : 5) as provision}
									<div
										role="button"
										tabindex="0"
										onclick={(e) => navigateToProvision(provision, e)}
										onkeydown={(e) => {
											if (e.key === 'Enter' || e.key === ' ') {
												e.preventDefault();
												navigateToProvision(provision, e);
											}
										}}
										use:prefetch={{ provisionId: provision.provision_id, year: provision.year }}
										class="w-full text-left border border-neutral-200 dark:border-neutral-800 rounded-lg p-4 bg-white dark:bg-neutral-950 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors cursor-pointer"
									>
										<div class="flex items-start gap-3 mb-2">
											<div class="w-1 h-1 rounded-full bg-neutral-400 dark:bg-neutral-600 mt-2 flex-shrink-0"></div>
											<div class="flex-1">
												<div class="font-mono text-xs text-neutral-500 dark:text-neutral-400 mb-1">
													{provision.provision_id}
												</div>
												<div class="text-sm text-neutral-700 dark:text-neutral-300">
													{provision.heading || provision.text_content.substring(0, 100)}...
												</div>
											</div>
										</div>

										<!-- Action Buttons -->
										<div class="flex gap-2 pt-2 border-t border-neutral-200 dark:border-neutral-800" onclick={(e) => e.stopPropagation()}>
											<button
												onclick={(e) => navigateToProvision(provision, e)}
												class="text-xs px-3 py-1.5 rounded-md bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-50 transition-colors"
											>
												View Full
											</button>
											<button
												onclick={(e) => viewInGraph(provision, e)}
												class="text-xs px-3 py-1.5 rounded-md bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-50 transition-colors"
											>
												View in Graph
											</button>
											<button
												onclick={(e) => compareVersions(provision, e)}
												class="text-xs px-3 py-1.5 rounded-md bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-50 transition-colors"
											>
												Compare
											</button>
										</div>
									</div>
								{/each}

								{#if provisions.length > 5 && !expanded}
									<button
										onclick={() => (expanded = true)}
										class="text-xs text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors mt-2"
									>
										Show all {provisions.length} provisions
									</button>
								{/if}
							</div>
						{:else}
							<div class="text-sm text-neutral-500 dark:text-neutral-400">
								No provisions found for this year.
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
