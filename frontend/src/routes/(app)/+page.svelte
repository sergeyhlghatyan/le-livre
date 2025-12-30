<script lang="ts">
	import { goto } from '$app/navigation';
	import { workspace } from '$lib/stores/workspace.svelte';
	import { Search, GitCompare, Clock } from 'lucide-svelte';

	const sections = [
		{
			id: '922',
			title: 'Title 18 USC § 922',
			description: 'Unlawful Acts',
			subtitle: 'Firearms regulations and prohibited acts'
		}
	];

	function openSearch() {
		// Trigger command palette via workspace or direct event
		const event = new KeyboardEvent('keydown', {
			key: 'k',
			metaKey: true,
			bubbles: true
		});
		window.dispatchEvent(event);
	}

	function viewSection(sectionId: string) {
		goto(`/section/${sectionId}`);
	}
</script>

<div class="flex flex-col h-full overflow-y-auto bg-neutral-50 dark:bg-neutral-900">
	<div class="max-w-6xl mx-auto px-6 py-12 w-full">
		<!-- Hero Section -->
		<div class="text-center mb-16">
			<h1 class="text-5xl font-bold text-neutral-900 dark:text-neutral-50 mb-4">
				Le Livre
			</h1>
			<p class="text-xl text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
				Find, compare, and track US Code provisions across time
			</p>
		</div>

		<!-- Quick Actions -->
		<div class="grid md:grid-cols-3 gap-6 mb-20">
			<!-- Search -->
			<button
				onclick={openSearch}
				class="group p-8 bg-white dark:bg-neutral-900 rounded-xl border-2 border-neutral-200 dark:border-neutral-800 hover:border-primary hover:shadow-lift transition-all text-left"
			>
				<div class="mb-4 text-neutral-400 group-hover:text-primary transition-colors">
					<Search class="w-12 h-12" />
				</div>
				<h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
					Search Provisions
				</h3>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					Find provisions by keyword or reference
				</p>
				<div class="mt-4 text-xs text-neutral-500">
					Press <kbd class="px-2 py-1 bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">⌘K</kbd> to search
				</div>
			</button>

			<!-- Compare -->
			<button
				onclick={() => goto('/compare')}
				class="group p-8 bg-white dark:bg-neutral-900 rounded-xl border-2 border-neutral-200 dark:border-neutral-800 hover:border-primary hover:shadow-lift transition-all text-left"
			>
				<div class="mb-4 text-neutral-400 group-hover:text-primary transition-colors">
					<GitCompare class="w-12 h-12" />
				</div>
				<h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
					Compare Versions
				</h3>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					See how provisions have changed across years
				</p>
			</button>

			<!-- Timeline -->
			<button
				onclick={() => goto('/timeline')}
				class="group p-8 bg-white dark:bg-neutral-900 rounded-xl border-2 border-neutral-200 dark:border-neutral-800 hover:border-primary hover:shadow-lift transition-all text-left"
			>
				<div class="mb-4 text-neutral-400 group-hover:text-primary transition-colors">
					<Clock class="w-12 h-12" />
				</div>
				<h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
					Browse Timeline
				</h3>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					View provisions by year and track changes
				</p>
			</button>
		</div>

		<!-- Browse Sections -->
		<div>
			<h2 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-6">
				Browse Sections
			</h2>

			<div class="space-y-4">
				{#each sections as section}
					<button
						onclick={() => viewSection(section.id)}
						class="w-full text-left p-6 bg-white dark:bg-neutral-800 rounded-xl border-2 border-neutral-200 dark:border-neutral-700 hover:border-primary hover:shadow-md transition-all group"
					>
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<h3 class="text-xl font-semibold text-neutral-900 dark:text-neutral-50 mb-2 group-hover:text-primary transition-colors">
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
									class="w-6 h-6 text-neutral-400 group-hover:text-primary transition-colors"
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

			<!-- Info Footer -->
			<div class="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
				<p class="text-sm text-blue-900 dark:text-blue-100">
					<strong>Note:</strong> More sections will be added as they become available.
				</p>
			</div>
		</div>
	</div>
</div>
