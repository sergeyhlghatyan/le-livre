import { browser } from '$app/environment';
import type { ChatResponse } from '$lib/api';

export interface Message {
	id: string;
	type: 'user' | 'assistant';
	content: string;
	timestamp: Date;
	response?: ChatResponse;
	loading?: boolean;
}

export interface Conversation {
	id: string;
	title: string;
	messages: Message[];
	createdAt: Date;
	updatedAt: Date;
}

class ChatStore {
	conversations = $state<Conversation[]>([]);
	activeConversationId = $state<string | null>(null);

	// Derived state for active conversation
	activeConversation = $derived(
		this.conversations.find((c) => c.id === this.activeConversationId) || null
	);

	// Legacy getter for backward compatibility
	get messages(): Message[] {
		return this.activeConversation?.messages || [];
	}

	constructor() {
		if (browser) {
			this.load();
		}
	}

	/**
	 * Create a new conversation
	 */
	createConversation(title?: string): string {
		const id = crypto.randomUUID();
		const conversation: Conversation = {
			id,
			title: title || 'New Conversation',
			messages: [],
			createdAt: new Date(),
			updatedAt: new Date()
		};

		this.conversations = [...this.conversations, conversation];
		this.activeConversationId = id;
		this.save();
		return id;
	}

	/**
	 * Switch to a different conversation
	 */
	switchConversation(id: string): void {
		const conversation = this.conversations.find((c) => c.id === id);
		if (conversation) {
			this.activeConversationId = id;
			this.saveActiveId();
		}
	}

	/**
	 * Delete a conversation
	 */
	deleteConversation(id: string): void {
		this.conversations = this.conversations.filter((c) => c.id !== id);

		// If we deleted the active conversation, switch to another
		if (this.activeConversationId === id) {
			if (this.conversations.length > 0) {
				this.activeConversationId = this.conversations[0].id;
			} else {
				// Create a new conversation if none left
				this.createConversation();
			}
		}

		this.save();
		this.saveActiveId();
	}

	/**
	 * Add a user message to the active conversation
	 */
	addUserMessage(content: string, conversationId?: string): string {
		const targetId = conversationId || this.activeConversationId;

		// Create a new conversation if none exists
		if (!targetId || !this.conversations.find((c) => c.id === targetId)) {
			this.createConversation();
		}

		const id = crypto.randomUUID();
		const message: Message = {
			id,
			type: 'user',
			content,
			timestamp: new Date()
		};

		this.conversations = this.conversations.map((conv) => {
			if (conv.id === (targetId || this.activeConversationId)) {
				// Auto-generate title from first message
				const title =
					conv.messages.length === 0
						? this.generateTitle(content)
						: conv.title;

				return {
					...conv,
					title,
					messages: [...conv.messages, message],
					updatedAt: new Date()
				};
			}
			return conv;
		});

		this.save();
		return id;
	}

	/**
	 * Add an assistant message to the active conversation
	 */
	addAssistantMessage(content: string, response?: ChatResponse): string {
		if (!this.activeConversationId) {
			this.createConversation();
		}

		const id = crypto.randomUUID();
		const message: Message = {
			id,
			type: 'assistant',
			content,
			timestamp: new Date(),
			response
		};

		this.conversations = this.conversations.map((conv) =>
			conv.id === this.activeConversationId
				? {
						...conv,
						messages: [...conv.messages, message],
						updatedAt: new Date()
					}
				: conv
		);

		this.save();
		return id;
	}

	/**
	 * Add a loading message
	 */
	addLoadingMessage(): string {
		if (!this.activeConversationId) {
			this.createConversation();
		}

		const id = crypto.randomUUID();
		const message: Message = {
			id,
			type: 'assistant',
			content: '',
			timestamp: new Date(),
			loading: true
		};

		this.conversations = this.conversations.map((conv) =>
			conv.id === this.activeConversationId
				? { ...conv, messages: [...conv.messages, message] }
				: conv
		);

		return id;
	}

	/**
	 * Update a message in the active conversation
	 */
	updateMessage(id: string, updates: Partial<Message>) {
		this.conversations = this.conversations.map((conv) =>
			conv.id === this.activeConversationId
				? {
						...conv,
						messages: conv.messages.map((msg) =>
							msg.id === id ? { ...msg, ...updates } : msg
						),
						updatedAt: new Date()
					}
				: conv
		);
		this.save();
	}

	/**
	 * Remove a message from the active conversation
	 */
	removeMessage(id: string) {
		this.conversations = this.conversations.map((conv) =>
			conv.id === this.activeConversationId
				? {
						...conv,
						messages: conv.messages.filter((msg) => msg.id !== id),
						updatedAt: new Date()
					}
				: conv
		);
		this.save();
	}

	/**
	 * Clear messages in the active conversation
	 */
	clear() {
		this.conversations = this.conversations.map((conv) =>
			conv.id === this.activeConversationId
				? {
						...conv,
						messages: [],
						updatedAt: new Date()
					}
				: conv
		);
		this.save();
	}

	/**
	 * Generate a title from the first message (50 chars max)
	 */
	private generateTitle(content: string): string {
		const maxLength = 50;
		if (content.length <= maxLength) {
			return content;
		}

		// Truncate at word boundary
		const truncated = content.substring(0, maxLength);
		const lastSpace = truncated.lastIndexOf(' ');
		return lastSpace > 0 ? truncated.substring(0, lastSpace) + '...' : truncated + '...';
	}

	/**
	 * Load conversations from localStorage
	 */
	private load(): void {
		if (!browser) return;

		try {
			// Check for legacy chat_history and migrate
			const legacyStored = localStorage.getItem('chat_history');
			if (legacyStored) {
				this.migrateLegacyChat(legacyStored);
				localStorage.removeItem('chat_history');
				return;
			}

			// Load conversations
			const conversationsStored = localStorage.getItem('chat_conversations');
			if (conversationsStored) {
				const parsed = JSON.parse(conversationsStored);
				this.conversations = parsed.map((conv: any) => ({
					...conv,
					messages: conv.messages.map((msg: any) => ({
						...msg,
						timestamp: new Date(msg.timestamp)
					})),
					createdAt: new Date(conv.createdAt),
					updatedAt: new Date(conv.updatedAt)
				}));
			}

			// Load active conversation ID
			const activeIdStored = localStorage.getItem('chat_active_id');
			if (activeIdStored) {
				this.activeConversationId = activeIdStored;
			}

			// Create default conversation if none exists
			if (this.conversations.length === 0) {
				this.createConversation();
			}
		} catch (e) {
			console.error('Failed to load chat conversations:', e);
			this.createConversation();
		}
	}

	/**
	 * Migrate legacy chat_history to new conversation format
	 */
	private migrateLegacyChat(legacyStored: string): void {
		try {
			const parsed = JSON.parse(legacyStored);
			const messages = parsed.map((msg: any) => ({
				...msg,
				timestamp: new Date(msg.timestamp)
			}));

			if (messages.length > 0) {
				const id = crypto.randomUUID();
				const conversation: Conversation = {
					id,
					title: 'Legacy Chat',
					messages,
					createdAt: new Date(messages[0].timestamp),
					updatedAt: new Date(messages[messages.length - 1].timestamp)
				};

				this.conversations = [conversation];
				this.activeConversationId = id;
				this.save();
				this.saveActiveId();
			}
		} catch (e) {
			console.error('Failed to migrate legacy chat:', e);
		}
	}

	/**
	 * Save conversations to localStorage
	 */
	private save() {
		if (!browser) return;

		try {
			localStorage.setItem('chat_conversations', JSON.stringify(this.conversations));

			// Auto-prune if we hit quota limit
		} catch (e: any) {
			if (e.name === 'QuotaExceededError') {
				this.pruneOldConversations();
				// Try saving again after pruning
				try {
					localStorage.setItem('chat_conversations', JSON.stringify(this.conversations));
				} catch (retryError) {
					console.error('Failed to save after pruning:', retryError);
				}
			} else {
				console.error('Failed to save chat conversations:', e);
			}
		}
	}

	/**
	 * Save active conversation ID
	 */
	private saveActiveId() {
		if (!browser) return;

		try {
			if (this.activeConversationId) {
				localStorage.setItem('chat_active_id', this.activeConversationId);
			}
		} catch (e) {
			console.error('Failed to save active conversation ID:', e);
		}
	}

	/**
	 * Prune oldest conversations, keeping 10 most recent
	 */
	private pruneOldConversations(): void {
		const maxConversations = 10;
		if (this.conversations.length <= maxConversations) return;

		// Sort by updatedAt descending
		const sorted = [...this.conversations].sort(
			(a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
		);

		// Keep only the 10 most recent
		this.conversations = sorted.slice(0, maxConversations);

		// Ensure active conversation is still valid
		if (
			this.activeConversationId &&
			!this.conversations.find((c) => c.id === this.activeConversationId)
		) {
			this.activeConversationId = this.conversations[0]?.id || null;
		}
	}
}

export const chat = new ChatStore();
