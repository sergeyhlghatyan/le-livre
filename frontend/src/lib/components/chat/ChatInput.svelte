<script lang="ts">
	import { chat } from '$lib/stores/chat.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	interface Props {
		onSubmit: (query: string) => void | Promise<void>;
		compact?: boolean;
		placeholder?: string;
		showClearButton?: boolean;
		onClear?: () => void;
	}

	let {
		onSubmit,
		compact = false,
		placeholder = 'Ask about firearms law...',
		showClearButton = false,
		onClear = () => {}
	}: Props = $props();

	let query = $state('');

	async function handleSubmit() {
		if (!query.trim()) return;

		const userQuestion = query.trim();
		query = '';

		await onSubmit(userQuestion);
	}

	function handleClear() {
		onClear();
	}
</script>

<form
	onsubmit={(e) => {
		e.preventDefault();
		handleSubmit();
	}}
	class={compact ? '' : 'max-w-chat mx-auto'}
>
	<div class="flex gap-2 items-end">
		{#if showClearButton && chat.messages.length > 0}
			<Button type="button" variant="ghost" onclick={handleClear} class={compact ? 'text-xs px-2 py-1' : ''}>
				Clear
			</Button>
		{/if}
		<input
			bind:value={query}
			type="text"
			{placeholder}
			class="flex-1 px-4 py-2.5 {compact ? 'text-xs' : 'text-sm'} border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors"
			onkeydown={(e) => {
				if (e.key === 'Enter' && !e.shiftKey) {
					e.preventDefault();
					handleSubmit();
				}
			}}
		/>
		<Button type="submit" variant="primary" disabled={!query.trim()} class={compact ? 'text-xs px-3 py-1.5' : ''}>
			→
		</Button>
	</div>
	{#if !compact}
		<p class="text-xs text-neutral-500 dark:text-neutral-400 mt-2 text-center">
			Press Enter to send
		</p>
	{/if}
</form>
