<script lang="ts">
	import { chat } from '$lib/stores/chat.svelte';
	import { workspace } from '$lib/stores/workspace.svelte';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast.svelte';
	import MessageBubble from './chat/MessageBubble.svelte';
	import ConversationSwitcher from './chat/ConversationSwitcher.svelte';
	import ChatInput from './chat/ChatInput.svelte';
	import { X } from 'lucide-svelte';

	let messagesContainer: HTMLDivElement;

	// Auto-scroll to bottom when messages change
	$effect(() => {
		const messages = chat.activeConversation?.messages;
		if (messages && messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	});

	async function handleSubmit(userQuestion: string) {
		// Add user message
		chat.addUserMessage(userQuestion);

		// Add loading message
		const loadingId = chat.addLoadingMessage();

		try {
			const response = await api.chat({ query: userQuestion, limit: 10 });

			// Remove loading message and add assistant response
			chat.removeMessage(loadingId);
			chat.addAssistantMessage(response.answer, response);
		} catch (err) {
			// Remove loading message
			chat.removeMessage(loadingId);

			// Show error toast
			const errorMessage = err instanceof Error ? err.message : 'An error occurred';
			toasts.error(errorMessage);

			// Add error message to chat
			chat.addAssistantMessage(
				`I apologize, but I encountered an error: ${errorMessage}. Please try again.`
			);
		}
	}

	function clearHistory() {
		if (confirm('Are you sure you want to clear messages in this conversation?')) {
			chat.clear();
			toasts.success('Conversation cleared');
		}
	}
</script>

<div class="flex flex-col h-full bg-white dark:bg-neutral-950">
	<!-- Header: Conversation Switcher + Close -->
	<div class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 p-4">
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-sm font-medium text-neutral-900 dark:text-neutral-50">Chat</h2>
			<button
				type="button"
				onclick={() => workspace.toggleSidebar()}
				class="p-1 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded transition-colors"
				aria-label="Close sidebar"
			>
				<X class="w-4 h-4 text-neutral-500 dark:text-neutral-400" />
			</button>
		</div>
		<ConversationSwitcher />
	</div>

	<!-- Messages (scrollable) -->
	<div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-4 space-y-4">
		{#if chat.activeConversation}
			{#if chat.activeConversation.messages.length === 0}
				<div class="text-center py-8">
					<p class="text-sm text-neutral-500 dark:text-neutral-400">
						No messages yet. Start a conversation!
					</p>
				</div>
			{:else}
				{#each chat.activeConversation.messages as message (message.id)}
					<MessageBubble {message} />
				{/each}
			{/if}
		{:else}
			<div class="text-center py-8">
				<p class="text-sm text-neutral-500 dark:text-neutral-400">No active conversation</p>
			</div>
		{/if}
	</div>

	<!-- Input (fixed at bottom) -->
	<div class="flex-shrink-0 border-t border-neutral-200 dark:border-neutral-800 p-4">
		<ChatInput
			onSubmit={handleSubmit}
			compact={true}
			showClearButton={true}
			onClear={clearHistory}
		/>
	</div>
</div>
