<script lang="ts">
	import { goto } from '$app/navigation';

	export interface BreadcrumbItem {
		label: string;
		href?: string;
	}

	interface Props {
		items: BreadcrumbItem[];
	}

	let { items }: Props = $props();

	function handleClick(item: BreadcrumbItem, e: MouseEvent) {
		if (item.href) {
			e.preventDefault();
			goto(item.href);
		}
	}
</script>

<nav aria-label="Breadcrumb" class="flex items-center gap-2 text-xs font-mono">
	{#each items as item, i}
		{#if i > 0}
			<span class="text-neutral-400 dark:text-neutral-600">/</span>
		{/if}
		{#if item.href && i < items.length - 1}
			<a
				href={item.href}
				onclick={(e) => handleClick(item, e)}
				class="text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
			>
				{item.label}
			</a>
		{:else}
			<span class="text-neutral-900 dark:text-neutral-50 font-medium">
				{item.label}
			</span>
		{/if}
	{/each}
</nav>
