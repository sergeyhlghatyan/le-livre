<script lang="ts">
	interface Props {
		id?: string;
		type?: 'text' | 'email' | 'password' | 'number' | 'search';
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		oninput?: (e: Event) => void;
		onchange?: (e: Event) => void;
	}

	let {
		id,
		type = 'text',
		value = $bindable(''),
		placeholder = '',
		disabled = false,
		oninput,
		onchange
	}: Props = $props();
</script>

<input
	{id}
	{type}
	bind:value
	{placeholder}
	{disabled}
	{oninput}
	{onchange}
	class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors disabled:opacity-50"
/>
