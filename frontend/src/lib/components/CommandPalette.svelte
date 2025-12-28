<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	interface SearchResult {
		provision_id: string;
		section_num: string;
		year: number;
		provision_level: string;
		provision_num: string;
		text_content: string;
		heading?: string;
		similarity?: number;
		relationship?: string;
		found_via?: string[];
	}

	interface SearchResponse {
		query: string;
		semantic_count: number;
		graph_count: number;
		both_count: number;
		total_results: number;
		results: SearchResult[];
	}

	interface Props {
		open: boolean;
		onClose: () => void;
	}

	let { open, onClose }: Props = $props();

	let query = $state('');
	let results = $state<SearchResult[]>([]);
	let selectedIndex = $state(0);
	let loading = $state(false);
	let searchInput: HTMLInputElement;
	let recentSearches = $state<string[]>([]);

	// Load recent searches from localStorage
	onMount(() => {
		const stored = localStorage.getItem('recentSearches');
		if (stored) {
			recentSearches = JSON.parse(stored);
		}
	});

	// Focus input when modal opens
	$effect(() => {
		if (open && searchInput) {
			searchInput.focus();
		}
	});

	// Perform search with debouncing
	let searchTimeout: number | undefined;
	async function performSearch() {
		if (!query.trim()) {
			results = [];
			return;
		}

		loading = true;
		clearTimeout(searchTimeout);

		searchTimeout = window.setTimeout(async () => {
			try {
				const response = await fetch(
					`http://localhost:8000/provisions/search?q=${encodeURIComponent(query)}&limit=10`
				);

				if (!response.ok) {
					throw new Error('Search failed');
				}

				const data: SearchResponse = await response.json();
				results = data.results;
				selectedIndex = 0;
			} catch (err) {
				console.error('Search error:', err);
				results = [];
			} finally {
				loading = false;
			}
		}, 300); // 300ms debounce
	}

	// Watch query changes
	$effect(() => {
		if (query) {
			performSearch();
		}
	});

	// Handle keyboard navigation
	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		} else if (e.key === 'ArrowDown') {
			e.preventDefault();
			selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selectedIndex = Math.max(selectedIndex - 1, 0);
		} else if (e.key === 'Enter' && results.length > 0) {
			e.preventDefault();
			selectResult(results[selectedIndex]);
		}
	}

	// Select a result
	function selectResult(result: SearchResult) {
		// Add to recent searches
		if (!recentSearches.includes(query)) {
			recentSearches = [query, ...recentSearches.slice(0, 9)]; // Keep last 10
			localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
		}

		// Navigate to provision
		goto(`/provision/${encodeURIComponent(result.provision_id)}?year=${result.year}`);
		onClose();
	}

	// Handle backdrop click
	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	// Truncate text for display
	function truncate(text: string, maxLength: number = 120): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	// Get badge color based on found_via
	function getBadgeClass(foundVia: string[] | undefined): string {
		if (!foundVia) return 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400';
		if (foundVia.length > 1) return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300';
		if (foundVia.includes('semantic')) return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
		if (foundVia.includes('graph')) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
		return 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400';
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div
		role="dialog"
		aria-modal="true"
		aria-labelledby="command-palette-title"
		onclick={handleBackdropClick}
		class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-start justify-center z-50 pt-20"
	>
		<div
			class="bg-white dark:bg-neutral-900 rounded-lg shadow-2xl w-full max-w-2xl mx-4 overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Search Input -->
			<div class="p-4 border-b border-neutral-200 dark:border-neutral-800">
				<input
					bind:this={searchInput}
					bind:value={query}
					type="text"
					placeholder="Search provisions... (⌘K)"
					class="w-full px-4 py-2 bg-neutral-50 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-md text-neutral-900 dark:text-neutral-50 placeholder-neutral-500 dark:placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary"
				/>
			</div>

			<!-- Results -->
			<div class="max-h-96 overflow-y-auto">
				{#if loading}
					<div class="p-8 text-center">
						<div class="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
						<p class="mt-2 text-sm text-neutral-500 dark:text-neutral-400">Searching...</p>
					</div>
				{:else if query && results.length === 0}
					<div class="p-8 text-center">
						<p class="text-sm text-neutral-500 dark:text-neutral-400">No results found for "{query}"</p>
					</div>
				{:else if results.length > 0}
					<div class="py-2">
						{#each results as result, index}
							<button
								type="button"
								onclick={() => selectResult(result)}
								onmouseenter={() => (selectedIndex = index)}
								class="w-full text-left px-4 py-3 hover:bg-neutral-100 dark:hover:bg-neutral-800 {selectedIndex === index
									? 'bg-neutral-100 dark:bg-neutral-800'
									: ''} transition-colors"
							>
								<div class="flex items-start gap-3">
									<div class="flex-1 min-w-0">
										<!-- Provision ID and Year -->
										<div class="flex items-center gap-2 mb-1">
											<span class="text-sm font-mono font-medium text-neutral-900 dark:text-neutral-50">
												{result.provision_id}
											</span>
											<span class="text-xs text-neutral-500 dark:text-neutral-400">
												({result.year})
											</span>
											{#if result.found_via}
												<span class="text-xs px-2 py-0.5 rounded {getBadgeClass(result.found_via)}">
													{result.found_via.join(' + ')}
												</span>
											{/if}
										</div>

										<!-- Heading -->
										{#if result.heading}
											<div class="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
												{result.heading}
											</div>
										{/if}

										<!-- Text Content Preview -->
										<div class="text-xs text-neutral-600 dark:text-neutral-400">
											{truncate(result.text_content)}
										</div>

										<!-- Similarity Score or Relationship -->
										{#if result.similarity}
											<div class="text-xs text-neutral-500 dark:text-neutral-500 mt-1">
												Similarity: {(result.similarity * 100).toFixed(0)}%
											</div>
										{:else if result.relationship}
											<div class="text-xs text-neutral-500 dark:text-neutral-500 mt-1">
												Relationship: {result.relationship}
											</div>
										{/if}
									</div>

									<!-- Arrow indicator -->
									{#if selectedIndex === index}
										<div class="text-neutral-400 dark:text-neutral-600 mt-1">→</div>
									{/if}
								</div>
							</button>
						{/each}
					</div>
				{:else if !query && recentSearches.length > 0}
					<!-- Recent Searches -->
					<div class="p-4">
						<h3 class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase mb-2">
							Recent Searches
						</h3>
						<div class="space-y-1">
							{#each recentSearches as recent}
								<button
									type="button"
									onclick={() => (query = recent)}
									class="w-full text-left px-3 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md transition-colors"
								>
									{recent}
								</button>
							{/each}
						</div>
					</div>
				{:else}
					<!-- Empty State -->
					<div class="p-8 text-center">
						<p class="text-sm text-neutral-500 dark:text-neutral-400">
							Type to search across all provisions
						</p>
						<p class="text-xs text-neutral-400 dark:text-neutral-500 mt-2">
							Use ↑↓ to navigate, Enter to select, Esc to close
						</p>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="p-3 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950">
				<div class="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
					<div class="flex items-center gap-4">
						<div class="flex items-center gap-1">
							<kbd class="px-1.5 py-0.5 bg-white dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">↑↓</kbd>
							<span>navigate</span>
						</div>
						<div class="flex items-center gap-1">
							<kbd class="px-1.5 py-0.5 bg-white dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">↵</kbd>
							<span>select</span>
						</div>
						<div class="flex items-center gap-1">
							<kbd class="px-1.5 py-0.5 bg-white dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">esc</kbd>
							<span>close</span>
						</div>
					</div>
					{#if results.length > 0}
						<span>{results.length} results</span>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
