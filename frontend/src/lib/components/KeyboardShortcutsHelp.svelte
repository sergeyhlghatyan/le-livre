<script lang="ts">
	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	const shortcuts = [
		{ keys: '⌘K / Ctrl+K', description: 'Open search command palette' },
		{ keys: '⌘\\ / Ctrl+\\', description: 'Toggle chat sidebar' },
		{ keys: 'Escape', description: 'Close sidebar or modal' },
		{ keys: '?', description: 'Show keyboard shortcuts help' },
		{ keys: '↑ ↓', description: 'Navigate search results' },
		{ keys: 'Enter', description: 'Select search result' }
	];
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Modal overlay -->
<div
	class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
	onclick={onClose}
>
	<div
		class="bg-white dark:bg-neutral-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
		onclick={(e) => e.stopPropagation()}
	>
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
				Keyboard Shortcuts
			</h2>
			<button
				onclick={onClose}
				class="text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
				aria-label="Close"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="space-y-3">
			{#each shortcuts as { keys, description }}
				<div class="flex items-center justify-between">
					<span class="text-sm text-neutral-700 dark:text-neutral-300">
						{description}
					</span>
					<kbd class="px-2 py-1 text-xs font-mono bg-neutral-100 dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
						{keys}
					</kbd>
				</div>
			{/each}
		</div>

		<div class="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
			<p class="text-xs text-neutral-500 dark:text-neutral-400 text-center">
				Press <kbd class="px-1.5 py-0.5 text-xs font-mono bg-neutral-100 dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">?</kbd> to show this help
			</p>
		</div>
	</div>
</div>
