<script lang="ts">
	import { goto } from '$app/navigation';
	import { navigationStore } from '$lib/stores/navigation.svelte';
	import { Home, ChevronRight, X } from 'lucide-svelte';

	/**
	 * Navigate to a specific breadcrumb item by index
	 */
	function navigateToIndex(index: number) {
		const item = navigationStore.getAt(index);
		if (!item) return;

		// Navigate to the provision
		goto(`/provision/${encodeURIComponent(item.provisionId)}?year=${item.year}`);

		// Truncate breadcrumb stack at this index
		navigationStore.goToIndex(index);
	}

	/**
	 * Navigate to home page
	 */
	function navigateHome() {
		navigationStore.clear();
		goto('/');
	}

	/**
	 * Clear breadcrumb stack
	 */
	function clearBreadcrumbs() {
		navigationStore.clear();
	}
</script>

{#if navigationStore.stackSize > 0}
	<nav
		class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2"
		aria-label="Breadcrumb navigation"
	>
		<div class="max-w-7xl mx-auto">
			<ol
				class="flex items-center space-x-2 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600"
			>
				<!-- Home button -->
				<li>
					<button
						on:click={navigateHome}
						class="flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
						aria-label="Navigate to home"
					>
						<Home class="w-4 h-4" />
					</button>
				</li>

				<!-- Breadcrumb items -->
				{#each navigationStore.breadcrumbs as item, index}
					<li class="flex items-center space-x-2">
						<!-- Separator -->
						<ChevronRight class="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />

						<!-- Breadcrumb button -->
						<button
							on:click={() => navigateToIndex(index)}
							class="text-sm font-medium whitespace-nowrap transition-colors
                   {index === navigationStore.stackSize - 1
								? 'text-blue-600 dark:text-blue-400'
								: 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'}"
							aria-current={index === navigationStore.stackSize - 1 ? 'page' : undefined}
						>
							{item.heading || `Provision (${item.year})`}
						</button>
					</li>
				{/each}

				<!-- Clear button -->
				<li class="ml-auto pl-4">
					<button
						on:click={clearBreadcrumbs}
						class="flex items-center text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
						aria-label="Clear breadcrumb trail"
					>
						<X class="w-4 h-4" />
					</button>
				</li>
			</ol>
		</div>
	</nav>
{/if}

<style>
	/* Custom scrollbar for horizontal scrolling on mobile */
	.scrollbar-thin::-webkit-scrollbar {
		height: 4px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: transparent;
	}

	.scrollbar-thumb-gray-300::-webkit-scrollbar-thumb {
		background-color: rgb(209, 213, 219);
		border-radius: 4px;
	}

	.dark .scrollbar-thumb-gray-600::-webkit-scrollbar-thumb {
		background-color: rgb(75, 85, 99);
	}
</style>
