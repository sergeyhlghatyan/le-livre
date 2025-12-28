<script lang="ts">
	interface Props {
		variant?: 'ghost' | 'primary';
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		onclick?: (e: MouseEvent) => void;
		children?: import('svelte').Snippet;
	}

	let {
		variant = 'ghost',
		type = 'button',
		disabled = false,
		onclick,
		children
	}: Props = $props();

	const styles = {
		ghost: 'px-3 py-1.5 text-sm text-neutral-700 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors',
		primary: 'px-4 py-2 bg-primary text-white hover:bg-primary-hover rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
	};
</script>

<button {type} class={styles[variant]} {disabled} {onclick}>
	{#if children}
		{@render children()}
	{/if}
</button>
