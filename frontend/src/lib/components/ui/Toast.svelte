<script lang="ts">
	import { toasts } from '$lib/stores/toast.svelte';

	const icons = {
		success: '✓',
		error: '✕',
		warning: '⚠',
		info: 'ⓘ'
	};

	const styles = {
		success: 'bg-white dark:bg-neutral-950 text-success border-success',
		error: 'bg-white dark:bg-neutral-950 text-error border-error',
		warning: 'bg-white dark:bg-neutral-950 text-warning border-warning',
		info: 'bg-white dark:bg-neutral-950 text-primary border-primary'
	};

	function handleRemove(id: string) {
		toasts.remove(id);
	}
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2">
	{#each toasts.toasts as toast (toast.id)}
		<div class="min-w-80 max-w-md p-4 rounded-lg border {styles[toast.type]}">
			<div class="flex items-start gap-3">
				<div class="text-lg flex-shrink-0">{icons[toast.type]}</div>
				<div class="flex-1 text-sm text-neutral-900 dark:text-neutral-50">{toast.message}</div>
				<button
					onclick={() => handleRemove(toast.id)}
					class="flex-shrink-0 text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
					aria-label="Close notification"
				>
					×
				</button>
			</div>
		</div>
	{/each}
</div>
