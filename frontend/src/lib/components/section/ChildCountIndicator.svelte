<script lang="ts">
	interface Props {
		count: number;
	}

	let { count }: Props = $props();
</script>

{#if count > 0}
	<div class="child-count flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400">
		<svg class="icon w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
			<path
				d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
			/>
		</svg>
		<span class="text-xs">
			{count}
			{count === 1 ? 'child' : 'children'}
		</span>
	</div>
{/if}
