<script lang="ts">
	interface Props {
		level: string;
	}

	let { level }: Props = $props();

	function getLabelForLevel(level: string): string {
		const levelMap: Record<string, string> = {
			section: 'Section',
			subsection: 'Subsection',
			paragraph: 'Paragraph',
			clause: 'Clause',
			subclause: 'Subclause',
			item: 'Item'
		};

		return levelMap[level.toLowerCase()] || level;
	}

	function getColorClass(level: string): string {
		const colorMap: Record<string, string> = {
			section: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
			subsection: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
			paragraph: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
			clause: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
			subclause: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400',
			item: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
		};

		return colorMap[level.toLowerCase()] || colorMap.item;
	}
</script>

<span class="badge {getColorClass(level)} px-2 py-1 rounded text-xs font-semibold">
	{getLabelForLevel(level)}
</span>
