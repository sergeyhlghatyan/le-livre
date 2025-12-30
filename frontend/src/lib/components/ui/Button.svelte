<script lang="ts">
	interface Props {
		variant?: 'ghost' | 'primary';
		size?: 'sm' | 'md' | 'lg';
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		onclick?: (e: MouseEvent) => void;
		class?: string;
		children?: import('svelte').Snippet;
	}

	let {
		variant = 'ghost',
		size = 'md',
		type = 'button',
		disabled = false,
		onclick,
		class: className = '',
		children
	}: Props = $props();

	const variantStyles = {
		ghost: 'text-neutral-700 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-neutral-50 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors',
		primary: 'bg-primary text-white hover:bg-primary-hover rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
	};

	const sizeStyles = {
		sm: 'px-3 py-1.5 text-xs',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-3 text-base'
	};

	const classes = `${variantStyles[variant]} ${sizeStyles[size]} ${className}`.trim();
</script>

<button {type} class={classes} {disabled} {onclick}>
	{#if children}
		{@render children()}
	{/if}
</button>
