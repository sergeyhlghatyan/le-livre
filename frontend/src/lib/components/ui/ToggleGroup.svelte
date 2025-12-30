<script lang="ts">
	interface ToggleOption {
		value: string;
		label: string;
	}

	let {
		value = $bindable(''),
		options = [] as ToggleOption[]
	} = $props();
</script>

<div class="inline-flex border border-neutral-300 dark:border-neutral-700 rounded-lg overflow-hidden">
	{#each options as option}
		<button
			type="button"
			onclick={() => value = option.value}
			class="px-4 py-2 text-sm font-medium transition-colors {value === option.value
				? 'bg-primary text-white'
				: 'bg-white dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800'}"
		>
			{option.label}
		</button>
	{/each}
</div>
