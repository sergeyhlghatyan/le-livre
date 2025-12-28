<script lang="ts">
	import { chat } from '$lib/stores/chat.svelte';
	import { ChevronDown, Plus, Trash2 } from 'lucide-svelte';

	let dropdownOpen = $state(false);
	let deleteConfirmId = $state<string | null>(null);

	const sortedConversations = $derived(
		[...chat.conversations]
			.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
			.slice(0, 20) // Max 20 displayed
	);

	function createNew() {
		chat.createConversation();
		dropdownOpen = false;
	}

	function switchTo(id: string) {
		chat.switchConversation(id);
		dropdownOpen = false;
	}

	function confirmDelete(id: string, e: MouseEvent) {
		e.stopPropagation();
		deleteConfirmId = id;
	}

	function deleteConv(id: string) {
		chat.deleteConversation(id);
		deleteConfirmId = null;
	}

	// Close dropdown when clicking outside
	function handleClickOutside(event: MouseEvent) {
		if (dropdownOpen) {
			dropdownOpen = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="relative">
	<!-- Trigger Button -->
	<button
		type="button"
		onclick={(e) => {
			e.stopPropagation();
			dropdownOpen = !dropdownOpen;
		}}
		class="w-full flex items-center justify-between px-3 py-2 border border-neutral-200 dark:border-neutral-800 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
	>
		<span class="truncate text-sm text-neutral-900 dark:text-neutral-50">
			{chat.activeConversation?.title ?? 'Select Conversation'}
		</span>
		<ChevronDown class="w-4 h-4 text-neutral-400 flex-shrink-0 ml-2" />
	</button>

	<!-- Dropdown Menu -->
	{#if dropdownOpen}
		<div
			onclick={(e) => e.stopPropagation()}
			class="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto"
		>
			<!-- New Conversation Button -->
			<button
				type="button"
				onclick={createNew}
				class="w-full flex items-center gap-2 px-4 py-3 text-sm text-primary hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
			>
				<Plus class="w-4 h-4" />
				New Conversation
			</button>

			<div class="border-t border-neutral-200 dark:border-neutral-800"></div>

			<!-- Conversation List -->
			{#each sortedConversations as conv}
				<div
					class="flex items-center justify-between px-4 py-3 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors {conv.id ===
					chat.activeConversationId
						? 'bg-neutral-100 dark:bg-neutral-800'
						: ''}"
				>
					<button
						type="button"
						onclick={() => switchTo(conv.id)}
						class="flex-1 text-left min-w-0"
					>
						<div class="text-sm text-neutral-900 dark:text-neutral-50 truncate">
							{conv.title}
						</div>
						<div class="text-xs text-neutral-500 dark:text-neutral-400">
							{conv.messages.length} messages
						</div>
					</button>

					<button
						type="button"
						onclick={(e) => confirmDelete(conv.id, e)}
						class="p-1 hover:bg-neutral-200 dark:hover:bg-neutral-700 rounded ml-2 flex-shrink-0"
						aria-label="Delete conversation"
					>
						<Trash2 class="w-4 h-4 text-error" />
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Delete Confirmation Modal -->
{#if deleteConfirmId}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		onclick={() => (deleteConfirmId = null)}
	>
		<div
			class="bg-white dark:bg-neutral-950 p-6 rounded-lg shadow-xl max-w-sm border border-neutral-200 dark:border-neutral-800"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-lg font-medium mb-2 text-neutral-900 dark:text-neutral-50">
				Delete Conversation?
			</h3>
			<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
				This action cannot be undone.
			</p>
			<div class="flex gap-2 justify-end">
				<button
					type="button"
					onclick={() => (deleteConfirmId = null)}
					class="px-4 py-2 text-sm rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-50 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
				>
					Cancel
				</button>
				<button
					type="button"
					onclick={() => deleteConv(deleteConfirmId!)}
					class="px-4 py-2 text-sm rounded-lg bg-error text-white hover:bg-red-600 transition-colors"
				>
					Delete
				</button>
			</div>
		</div>
	</div>
{/if}
