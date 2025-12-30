<script lang="ts">
	interface Props {
		nodeCount: number;
		edgeCount: number;
	}

	let { nodeCount, edgeCount }: Props = $props();
</script>

<div
	class="absolute top-4 left-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg"
>
	<div class="space-y-1.5">
		<div class="flex items-center gap-2">
			<div class="w-2 h-2 rounded-full bg-blue-500"></div>
			<span class="text-xs text-neutral-700 dark:text-neutral-300">
				<span class="font-medium">{nodeCount}</span> nodes
			</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-2 h-2 rounded-full bg-neutral-400 dark:bg-neutral-500"></div>
			<span class="text-xs text-neutral-700 dark:text-neutral-300">
				<span class="font-medium">{edgeCount}</span> edges
			</span>
		</div>
	</div>
</div>
