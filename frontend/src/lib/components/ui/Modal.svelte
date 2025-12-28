<script lang="ts">
	interface Props {
		open?: boolean;
		onClose?: () => void;
		children?: import('svelte').Snippet;
	}

	let {
		open = $bindable(false),
		onClose,
		children
	}: Props = $props();

	function handleClose() {
		open = false;
		onClose?.();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && open) {
			handleClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/20 backdrop-blur-sm"
			onclick={handleClose}
			role="presentation"
		></div>

		<!-- Modal -->
		<div class="relative bg-white dark:bg-neutral-950 rounded-xl shadow-2xl max-w-2xl w-full mx-auto p-6 border border-neutral-200 dark:border-neutral-800">
			{#if children}
				{@render children()}
			{/if}
		</div>
	</div>
{/if}
