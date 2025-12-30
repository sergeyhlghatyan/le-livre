<script lang="ts">
	const levelColors = {
		section: '#3B82F6',
		subsection: '#10B981',
		paragraph: '#F59E0B',
		subparagraph: '#8B5CF6',
		clause: '#EC4899'
	};
</script>

<div
	class="absolute bottom-4 left-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 shadow-lg"
>
	<h4 class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-3">Legend</h4>

	<!-- Provision Levels -->
	<div class="space-y-2 mb-4">
		<p class="text-xs text-neutral-500 dark:text-neutral-400 font-medium">Provision Levels</p>
		{#each Object.entries(levelColors) as [level, color]}
			<div class="flex items-center gap-2">
				<div
					class="w-3 h-3 rounded-full"
					style="background-color: {color}; box-shadow: 0 0 0 2px {color}33;"
				></div>
				<span class="text-xs text-neutral-700 dark:text-neutral-300 capitalize">{level}</span>
			</div>
		{/each}
	</div>

	<!-- Relationships -->
	<div class="space-y-2">
		<p class="text-xs text-neutral-500 dark:text-neutral-400 font-medium">Relationships</p>
		<div class="flex items-center gap-2">
			<div class="w-6 h-0.5 bg-neutral-400 dark:bg-neutral-500"></div>
			<span class="text-xs text-neutral-700 dark:text-neutral-300">Parent/Child</span>
		</div>
		<div class="flex items-center gap-2">
			<div
				class="w-6 h-0.5 bg-neutral-400 dark:bg-neutral-500"
				style="background-image: linear-gradient(to right, currentColor 50%, transparent 50%); background-size: 4px 1px;"
			></div>
			<span class="text-xs text-neutral-700 dark:text-neutral-300">Reference</span>
		</div>
	</div>
</div>
