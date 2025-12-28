<script lang="ts">
	interface Props {
		length: number;
	}

	let { length }: Props = $props();

	function getLengthScore(textLength: number): number {
		// < 200: 1, 200-500: 2, 500-1000: 3, 1000-2000: 4, > 2000: 5
		if (textLength < 200) return 1;
		if (textLength < 500) return 2;
		if (textLength < 1000) return 3;
		if (textLength < 2000) return 4;
		return 5;
	}

	function getLengthLabel(score: number): string {
		const labels = ['', 'Short', 'Medium', 'Long', 'Very Long', 'Complex'];
		return labels[score] || '';
	}

	let lengthScore = $derived(getLengthScore(length));
</script>

<div class="text-length flex items-center gap-1">
	{#each Array(5) as _, i}
		<span class="dot {i < lengthScore ? 'filled' : 'empty'} text-sm">
			{i < lengthScore ? '●' : '○'}
		</span>
	{/each}
	<span class="label text-xs ml-1 text-neutral-600 dark:text-neutral-400">
		{getLengthLabel(lengthScore)}
	</span>
</div>

<style>
	.filled {
		@apply text-blue-600 dark:text-blue-400;
	}

	.empty {
		@apply text-neutral-300 dark:text-neutral-600;
	}
</style>
