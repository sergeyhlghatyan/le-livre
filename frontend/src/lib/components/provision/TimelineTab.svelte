<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Provision, type ProvisionContext, type TimelineChange } from '$lib/api';

	interface Props {
		provision: Provision;
		context: ProvisionContext;
		selectedYear: number;
		loadingYear?: boolean;
		onYearChange: (year: number) => void;
		onViewDiff?: (fromYear: number, toYear: number) => void;
	}

	let { provision, context, selectedYear, loadingYear = false, onYearChange, onViewDiff }: Props = $props();

	let timelineChanges = $state<TimelineChange[]>([]);
	let loading = $state(false);

	const years = context.timeline || [1994, 2000, 2006, 2013, 2018, 2022, 2024];

	onMount(async () => {
		await loadTimelineChanges();
	});

	async function loadTimelineChanges() {
		loading = true;
		try {
			timelineChanges = await api.getProvisionTimelineChanges(provision.provision_id);
		} catch (err) {
			console.error('Error loading timeline changes:', err);
			timelineChanges = [];
		} finally {
			loading = false;
		}
	}

	function getChangeForYear(year: number): TimelineChange | undefined {
		return timelineChanges.find(c => c.year === year);
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

	function getChangeLabel(changeType: string): string {
		switch (changeType) {
			case 'added':
				return 'Added';
			case 'modified':
				return 'Modified';
			case 'removed':
				return 'Removed';
			default:
				return 'Unchanged';
		}
	}

	function handleYearClick(year: number) {
		onYearChange(year);
	}

	function handleViewDiff(fromYear: number, toYear: number) {
		if (onViewDiff) {
			onViewDiff(fromYear, toYear);
		}
	}

	// Get previous year from timeline for comparison
	function getPreviousYear(year: number): number | null {
		const yearIndex = years.indexOf(year);
		if (yearIndex > 0) {
			return years[yearIndex - 1];
		}
		return null;
	}
</script>

<div class="space-y-8">
	<!-- Timeline visualization -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-8">
		<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
			Timeline
		</h2>

		{#if loading}
			<p class="text-neutral-500 dark:text-neutral-400">Loading timeline data...</p>
		{:else}
			<!-- Interactive timeline -->
			<div class="relative">
				<!-- Timeline line -->
				<div class="absolute top-6 left-0 right-0 h-0.5 bg-neutral-300 dark:bg-neutral-600"></div>

				<!-- Year markers -->
				<div class="relative flex justify-between">
					{#each years as year}
						{@const change = getChangeForYear(year)}
						<button
							onclick={() => handleYearClick(year)}
							disabled={loadingYear}
							class="flex flex-col items-center group cursor-pointer {loadingYear ? 'opacity-50 cursor-wait' : ''}"
						>
							<!-- Year dot -->
							<div class="relative">
								<div
									class="w-12 h-12 rounded-full border-4 border-white dark:border-neutral-950 transition-all
										{selectedYear === year
											? 'bg-blue-600 ring-4 ring-blue-200 dark:ring-blue-900 scale-110'
											: change
												? `${getChangeColor(change.change_type)} hover:scale-110`
												: 'bg-neutral-400 dark:bg-neutral-600 hover:scale-110'}"
								>
									{#if change && selectedYear !== year}
										<div class="absolute -top-1 -right-1 w-4 h-4 {getChangeColor(change.change_type)} rounded-full border-2 border-white dark:border-neutral-950"></div>
									{/if}
									{#if loadingYear && selectedYear === year}
										<div class="absolute inset-0 flex items-center justify-center">
											<span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
										</div>
									{/if}
								</div>
							</div>

							<!-- Year label -->
							<span class="mt-4 text-sm font-medium
								{selectedYear === year
									? 'text-neutral-900 dark:text-neutral-50'
									: 'text-neutral-600 dark:text-neutral-400 group-hover:text-neutral-900 dark:group-hover:text-neutral-50'}"
							>
								{year}
							</span>

							<!-- Change label -->
							{#if change && change.change_type !== 'unchanged'}
								<span class="mt-1 text-xs px-2 py-0.5 rounded-full
									{change.change_type === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
									change.change_type === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
									'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}"
								>
									{getChangeLabel(change.change_type)}
								</span>
							{/if}
						</button>
					{/each}
				</div>
			</div>

			<!-- Selected year details -->
			{@const selectedChange = getChangeForYear(selectedYear)}
			{#if selectedChange}
				<div class="mt-12 p-6 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700">
					<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
						{selectedYear} Details
					</h3>

					<div class="space-y-3">
						<div class="flex items-center gap-3">
							<span class="text-sm text-neutral-600 dark:text-neutral-400">Status:</span>
							<span class="text-sm px-3 py-1 rounded-full font-medium
								{selectedChange.change_type === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
								selectedChange.change_type === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
								selectedChange.change_type === 'removed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
								'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-400'}"
							>
								{getChangeLabel(selectedChange.change_type)}
							</span>
						</div>

						{#if selectedChange.magnitude !== undefined}
							<div class="flex items-center gap-3">
								<span class="text-sm text-neutral-600 dark:text-neutral-400">Change Magnitude:</span>
								<div class="flex-1 max-w-xs">
									<div class="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
										<div
											class="h-full transition-all
												{selectedChange.magnitude > 0.7 ? 'bg-red-500' :
												selectedChange.magnitude > 0.3 ? 'bg-amber-500' :
												'bg-green-500'}"
											style="width: {selectedChange.magnitude * 100}%"
										></div>
									</div>
								</div>
								<span class="text-sm text-neutral-600 dark:text-neutral-400">
									{Math.round(selectedChange.magnitude * 100)}%
								</span>
							</div>
						{/if}

						{#if selectedChange.text_delta !== undefined && selectedChange.text_delta > 0}
							<div class="flex items-center gap-3">
								<span class="text-sm text-neutral-600 dark:text-neutral-400">Text Change:</span>
								<span class="text-sm text-neutral-900 dark:text-neutral-50">
									{selectedChange.text_delta} characters
								</span>
							</div>
						{/if}
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<!-- Change History Section -->
	{#if !loading && timelineChanges.length > 0}
		{@const changesWithHistory = timelineChanges.filter(c => c.change_type !== 'unchanged')}
		{#if changesWithHistory.length > 0}
			<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
				<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
					Change History ({changesWithHistory.length})
				</h3>

				<div class="space-y-4">
					{#each changesWithHistory.sort((a, b) => b.year - a.year) as change}
						{@const prevYear = getPreviousYear(change.year)}
						<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700">
							<div class="flex items-start justify-between gap-4 mb-3">
								<div class="flex items-center gap-3">
									<div class="w-3 h-3 rounded-full {getChangeColor(change.change_type)}"></div>
									<span class="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
										{change.year}
									</span>
									<span class="text-sm px-2.5 py-0.5 rounded-full font-medium
										{change.change_type === 'added' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
										change.change_type === 'modified' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
										'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}"
									>
										{getChangeLabel(change.change_type)}
									</span>
								</div>

								{#if prevYear && change.change_type === 'modified'}
									<button
										onclick={() => handleViewDiff(prevYear, change.year)}
										class="px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors flex items-center gap-1"
									>
										View Full Diff
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										</svg>
									</button>
								{/if}
							</div>

							<div class="space-y-2 ml-6">
								{#if change.magnitude !== undefined && change.magnitude > 0}
									<div class="flex items-center gap-3">
										<span class="text-xs text-neutral-600 dark:text-neutral-400 w-24">Impact:</span>
										<div class="flex-1 max-w-xs h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
											<div
												class="h-full transition-all
													{change.magnitude > 0.7 ? 'bg-red-500' :
													change.magnitude > 0.3 ? 'bg-amber-500' :
													'bg-green-500'}"
												style="width: {change.magnitude * 100}%"
											></div>
										</div>
										<span class="text-xs text-neutral-600 dark:text-neutral-400">
											{Math.round(change.magnitude * 100)}%
										</span>
									</div>
								{/if}

								{#if change.text_delta !== undefined && change.text_delta !== 0}
									<div class="flex items-center gap-3">
										<span class="text-xs text-neutral-600 dark:text-neutral-400 w-24">Text Change:</span>
										<span class="text-xs text-neutral-900 dark:text-neutral-50">
											{change.text_delta > 0 ? '+' : ''}{change.text_delta} characters
										</span>
									</div>
								{/if}

								{#if change.change_type === 'added'}
									<p class="text-sm text-neutral-600 dark:text-neutral-400 italic">
										This provision was added in {change.year}
									</p>
								{:else if change.change_type === 'removed'}
									<p class="text-sm text-neutral-600 dark:text-neutral-400 italic">
										This provision was removed in {change.year}
									</p>
								{:else if change.change_type === 'modified'}
									<p class="text-sm text-neutral-600 dark:text-neutral-400">
										Modified from {prevYear || 'previous version'}
									</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}

	<!-- Change history legend -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
			Legend
		</h3>
		<div class="flex flex-wrap gap-4">
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 rounded-full bg-green-500"></div>
				<span class="text-sm text-neutral-600 dark:text-neutral-400">Added</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 rounded-full bg-amber-500"></div>
				<span class="text-sm text-neutral-600 dark:text-neutral-400">Modified</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 rounded-full bg-red-500"></div>
				<span class="text-sm text-neutral-600 dark:text-neutral-400">Removed</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 rounded-full bg-neutral-400 dark:bg-neutral-600"></div>
				<span class="text-sm text-neutral-600 dark:text-neutral-400">Unchanged</span>
			</div>
		</div>
	</div>
</div>
