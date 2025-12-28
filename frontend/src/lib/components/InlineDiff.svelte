<script lang="ts">
	import type { InlineDiffPart } from '$lib/api';

	interface Props {
		parts: InlineDiffPart[];
	}

	let { parts }: Props = $props();
</script>

<div class="inline-diff">
	{#each parts as part}
		{#if part.type === 'unchanged'}
			<span class="unchanged">{part.text}</span>
		{:else if part.type === 'added'}
			<span class="added">{part.text}</span>
		{:else if part.type === 'removed'}
			<span class="removed">{part.text}</span>
		{/if}
	{/each}
</div>

<style>
	.inline-diff {
		font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
		font-size: 0.875rem;
		line-height: 1.6;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.unchanged {
		color: #374151;
	}

	.added {
		background-color: #dcfce7;
		color: #166534;
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
	}

	.removed {
		background-color: #fee2e2;
		color: #991b1b;
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
		text-decoration: line-through;
	}
</style>
