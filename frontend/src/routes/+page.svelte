<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth.svelte';

	// Auth guard - redirect to login if not authenticated
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	const sections = [
		{
			id: '922',
			title: 'Title 18 USC § 922',
			description: 'Unlawful Acts',
			subtitle: 'Firearms regulations and prohibited acts'
		}
	];

	function viewSection(sectionId: string) {
		goto(`/section/${sectionId}`);
	}
</script>

{#if auth.loading}
	<div class="flex items-center justify-center h-full">
		<div class="text-neutral-500 dark:text-neutral-400">Loading...</div>
	</div>
{:else if !auth.isAuthenticated}
	<div class="flex items-center justify-center h-full">
		<div class="text-neutral-500 dark:text-neutral-400">Redirecting to login...</div>
	</div>
{:else}
	<div class="flex flex-col h-full bg-neutral-50 dark:bg-neutral-900">
		<div class="flex-1 overflow-y-auto">
			<div class="max-w-4xl mx-auto px-6 py-12">
				<!-- Header -->
				<div class="mb-12">
				<h1 class="text-3xl font-bold text-neutral-900 dark:text-neutral-50 mb-3">
					Le Livre
				</h1>
				<p class="text-neutral-600 dark:text-neutral-400">
					Browse US Code provisions with historical timeline tracking
				</p>
			</div>

			<!-- Sections List -->
			<div class="space-y-4">
				<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
					Available Sections
				</h2>

				{#each sections as section}
					<button
						onclick={() => viewSection(section.id)}
						class="w-full text-left p-6 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600 hover:shadow-md transition-all"
					>
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-1">
									{section.title}
								</h3>
								<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
									{section.description}
								</p>
								<p class="text-xs text-neutral-500 dark:text-neutral-500">
									{section.subtitle}
								</p>
							</div>
							<div class="ml-4">
								<svg
									class="w-6 h-6 text-neutral-400"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 5l7 7-7 7"
									/>
								</svg>
							</div>
						</div>
					</button>
				{/each}
			</div>

			<!-- Footer Info -->
			<div class="mt-12 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
				<p class="text-sm text-blue-900 dark:text-blue-100">
					<strong>Note:</strong> More sections will be added as they become available.
				</p>
			</div>
		</div>
	</div>
	</div>
{/if}
