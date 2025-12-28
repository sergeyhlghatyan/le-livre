<script lang="ts">
	interface Props {
		count: number;
	}

	let { count }: Props = $props();
</script>

{#if count > 1}
	<div
		class="revision-badge flex items-center gap-1.5 text-xs text-neutral-600 dark:text-neutral-400"
		title="This provision exists in {count} different years"
	>
		<svg class="icon w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
			<path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
		</svg>
		<span>
			📚 {count} {count === 2 ? 'revision' : 'revisions'}
		</span>
	</div>
{/if}
