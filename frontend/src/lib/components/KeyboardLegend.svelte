<script lang="ts">
	interface Props {
		open: boolean;
		onClose: () => void;
	}

	let { open, onClose }: Props = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div
		role="dialog"
		aria-modal="true"
		aria-labelledby="keyboard-legend-title"
		onclick={handleBackdropClick}
		class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
	>
		<div
			class="bg-white dark:bg-neutral-900 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="flex items-center justify-between mb-4">
				<h2 id="keyboard-legend-title" class="text-lg font-medium text-neutral-900 dark:text-neutral-50">
					Keyboard Shortcuts
				</h2>
				<button
					type="button"
					onclick={onClose}
					class="text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
					aria-label="Close"
				>
					✕
				</button>
			</div>

			<!-- Shortcuts List -->
			<div class="space-y-3">
				<div class="flex items-center justify-between py-2 border-b border-neutral-200 dark:border-neutral-800">
					<span class="text-sm text-neutral-700 dark:text-neutral-300">Next change</span>
					<kbd class="px-2 py-1 text-xs font-mono bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">
						j
					</kbd>
				</div>

				<div class="flex items-center justify-between py-2 border-b border-neutral-200 dark:border-neutral-800">
					<span class="text-sm text-neutral-700 dark:text-neutral-300">Previous change</span>
					<kbd class="px-2 py-1 text-xs font-mono bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">
						k
					</kbd>
				</div>

				<div class="flex items-center justify-between py-2 border-b border-neutral-200 dark:border-neutral-800">
					<span class="text-sm text-neutral-700 dark:text-neutral-300">Show this help</span>
					<kbd class="px-2 py-1 text-xs font-mono bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">
						?
					</kbd>
				</div>

				<div class="flex items-center justify-between py-2">
					<span class="text-sm text-neutral-700 dark:text-neutral-300">Close dialogs</span>
					<kbd class="px-2 py-1 text-xs font-mono bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">
						ESC
					</kbd>
				</div>
			</div>

			<!-- Footer -->
			<div class="mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-800">
				<button
					type="button"
					onclick={onClose}
					class="w-full px-4 py-2 bg-primary text-white rounded-md hover:opacity-90 transition-opacity text-sm font-medium"
				>
					Got it
				</button>
			</div>
		</div>
	</div>
{/if}
