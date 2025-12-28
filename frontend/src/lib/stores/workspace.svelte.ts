import { browser } from '$app/environment';
import { navigationStore } from './navigation.svelte';
import { chat } from './chat.svelte';

/**
 * Workspace state interface
 */
export interface WorkspaceState {
	sidebarOpen: boolean;
	sidebarWidth: number; // 320-600px
	currentProvisionId: string | null;
	currentYear: number | null;
	diffGranularity: 'word' | 'sentence';
}

/**
 * Encoded state for URL sharing
 */
interface EncodedState {
	p: string | null; // provision
	y: number | null; // year
	b: any[]; // breadcrumbs
	c: string | null; // conversation
	s: boolean; // sidebar state
}

/**
 * Debounce utility
 */
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
	let timeoutId: ReturnType<typeof setTimeout> | null = null;

	return ((...args: any[]) => {
		if (timeoutId !== null) {
			clearTimeout(timeoutId);
		}
		timeoutId = setTimeout(() => fn(...args), delay);
	}) as T;
}

/**
 * Workspace Store - Centralized UI state management
 *
 * Manages sidebar state, current provision context, and view preferences.
 * Persists to localStorage and supports URL encoding for sharing.
 */
class WorkspaceStore {
	state = $state<WorkspaceState>({
		sidebarOpen: false,
		sidebarWidth: 384, // w-96 in Tailwind
		currentProvisionId: null,
		currentYear: null,
		diffGranularity: 'word'
	});

	private storageKey = 'workspace_state';
	private debouncedSave = debounce(() => this.persist(), 500);

	constructor() {
		if (browser) {
			this.load();
		}
	}

	/**
	 * Toggle sidebar open/closed
	 */
	toggleSidebar(): void {
		this.state.sidebarOpen = !this.state.sidebarOpen;
		this.debouncedSave();
	}

	/**
	 * Set sidebar width (320-600px)
	 */
	setSidebarWidth(width: number): void {
		const clampedWidth = Math.max(320, Math.min(600, width));
		this.state.sidebarWidth = clampedWidth;
		this.debouncedSave();
	}

	/**
	 * Set current provision context (for prefetching)
	 */
	setCurrentProvision(provisionId: string | null, year: number | null): void {
		this.state.currentProvisionId = provisionId;
		this.state.currentYear = year;
		this.debouncedSave();
	}

	/**
	 * Set diff granularity preference
	 */
	setDiffGranularity(granularity: 'word' | 'sentence'): void {
		this.state.diffGranularity = granularity;
		this.debouncedSave();
	}

	/**
	 * Encode workspace state to URL-safe string
	 */
	encodeToUrl(): string {
		const encoded: EncodedState = {
			p: this.state.currentProvisionId,
			y: this.state.currentYear,
			b: navigationStore.breadcrumbs,
			c: chat.activeConversationId,
			s: this.state.sidebarOpen
		};

		return btoa(JSON.stringify(encoded));
	}

	/**
	 * Decode and restore workspace state from URL string
	 */
	decodeFromUrl(encoded: string): void {
		try {
			const state: EncodedState = JSON.parse(atob(encoded));

			// Restore workspace state
			if (state.p !== undefined) this.state.currentProvisionId = state.p;
			if (state.y !== undefined) this.state.currentYear = state.y;
			if (state.s !== undefined) this.state.sidebarOpen = state.s;

			// Restore breadcrumbs
			if (state.b && Array.isArray(state.b)) {
				navigationStore.breadcrumbs = state.b;
			}

			// Restore conversation
			if (state.c) {
				chat.switchConversation(state.c);
			}

			this.persist();
		} catch (e) {
			console.error('Failed to decode workspace state:', e);
		}
	}

	/**
	 * Load state from localStorage
	 */
	private load(): void {
		if (!browser) return;

		try {
			const stored = localStorage.getItem(this.storageKey);
			if (stored) {
				const parsed = JSON.parse(stored) as WorkspaceState;
				this.state = { ...this.state, ...parsed };
			}
		} catch (e) {
			console.error('Failed to load workspace state:', e);
		}
	}

	/**
	 * Persist state to localStorage
	 */
	private persist(): void {
		if (!browser) return;

		try {
			localStorage.setItem(this.storageKey, JSON.stringify(this.state));
		} catch (e) {
			console.error('Failed to persist workspace state:', e);
		}
	}
}

// Singleton instance
export const workspace = new WorkspaceStore();
