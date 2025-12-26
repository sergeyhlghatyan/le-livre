<script lang="ts">
	import { api, type Provision } from '$lib/api';
	import { onMount } from 'svelte';

	let section = $state('922');
	let years = $state<number[]>([]);
	let selectedYear = $state<number>(0);
	let provisions = $state<Provision[]>([]);
	let loading = $state(false);
	let error = $state('');

	onMount(async () => {
		await loadTimeline();
	});

	async function loadTimeline() {
		loading = true;
		error = '';

		try {
			const timeline = await api.getTimeline(section);
			years = timeline.years;
			if (years.length > 0) {
				selectedYear = years[years.length - 1]; // Default to latest year
				await loadProvisions();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load timeline';
		} finally {
			loading = false;
		}
	}

	async function loadProvisions() {
		if (!selectedYear) return;

		loading = true;
		error = '';

		try {
			provisions = await api.getProvisions(section, selectedYear);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load provisions';
		} finally {
			loading = false;
		}
	}

	function handleYearChange() {
		loadProvisions();
	}
</script>

<div class="px-4 py-6">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-2">Timeline View</h1>
		<p class="text-gray-600">Explore how provisions evolved over time</p>
	</div>

	<!-- Section Selector -->
	<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
		<label for="section" class="block text-sm font-medium text-gray-700 mb-2">
			Section
		</label>
		<div class="flex gap-4">
			<input
				id="section"
				type="text"
				bind:value={section}
				class="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
				placeholder="922"
			/>
			<button
				onclick={loadTimeline}
				class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
			>
				Load Timeline
			</button>
		</div>
	</div>

	<!-- Error Message -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
			<p class="text-red-800">{error}</p>
		</div>
	{/if}

	<!-- Timeline Slider -->
	{#if years.length > 0}
		<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
			<div class="mb-4">
				<label for="year-slider" class="block text-sm font-medium text-gray-700 mb-2">
					Year: <span class="text-blue-600 font-semibold">{selectedYear}</span>
				</label>
				<input
					id="year-slider"
					type="range"
					min={0}
					max={years.length - 1}
					bind:value={selectedYear}
					onchange={handleYearChange}
					oninput={(e) => {
						const idx = parseInt(e.currentTarget.value);
						selectedYear = years[idx];
					}}
					class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
				/>
				<div class="flex justify-between text-xs text-gray-500 mt-2">
					{#each years as year}
						<span>{year}</span>
					{/each}
				</div>
			</div>
		</div>
	{/if}

	<!-- Loading State -->
	{#if loading}
		<div class="bg-white rounded-lg shadow-sm border p-8 text-center">
			<div class="text-gray-600">Loading...</div>
		</div>
	{/if}

	<!-- Provisions -->
	{#if !loading && provisions.length > 0}
		<div class="space-y-4">
			<h2 class="text-xl font-semibold text-gray-900">
				Provisions for Section {section} ({selectedYear})
			</h2>
			{#each provisions as provision}
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex items-start justify-between mb-3">
						<div>
							<h3 class="text-lg font-semibold text-gray-900">
								{provision.heading || provision.provision_id}
							</h3>
							<p class="text-sm text-gray-500">
								{provision.provision_id} • {provision.provision_level}
							</p>
						</div>
					</div>
					<div class="text-gray-700 whitespace-pre-wrap">
						{provision.text_content}
					</div>
				</div>
			{/each}
		</div>
	{:else if !loading && provisions.length === 0 && years.length > 0}
		<div class="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-600">
			No provisions found for this year.
		</div>
	{/if}
</div>
