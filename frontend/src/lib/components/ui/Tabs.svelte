<script lang="ts">
	export interface Tab {
		id: string;
		label: string;
		badge?: string | number;    // Optional badge (e.g., count)
		disabled?: boolean;
	}

	interface Props {
		tabs: Tab[];
		activeTab: string;
		onTabChange: (tabId: string) => void;
	}

	let { tabs, activeTab, onTabChange }: Props = $props();

	function handleKeydown(e: KeyboardEvent, tabId: string) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			onTabChange(tabId);
		}
	}
</script>

<div class="border-b border-neutral-200 dark:border-neutral-800">
	<nav class="-mb-px flex gap-6 overflow-x-auto" aria-label="Tabs">
		{#each tabs as tab}
			<button
				role="tab"
				aria-selected={activeTab === tab.id}
				disabled={tab.disabled}
				onclick={() => onTabChange(tab.id)}
				onkeydown={(e) => handleKeydown(e, tab.id)}
				class="
					relative py-3 px-1 text-sm font-medium transition-colors
					border-b-2 whitespace-nowrap
					{activeTab === tab.id
						? 'border-primary text-neutral-900 dark:text-neutral-50'
						: 'border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 hover:border-neutral-300 dark:hover:border-neutral-700'}
					{tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
				"
			>
				{tab.label}

				{#if tab.badge !== undefined}
					<span
						class="ml-2 px-2 py-0.5 text-xs rounded-full
							{activeTab === tab.id
								? 'bg-primary/10 text-primary'
								: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'}"
					>
						{tab.badge}
					</span>
				{/if}
			</button>
		{/each}
	</nav>
</div>
