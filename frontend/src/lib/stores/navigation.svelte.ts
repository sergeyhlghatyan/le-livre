/**
 * Navigation Store - Breadcrumb navigation with history tracking
 *
 * Tracks provision visits as a breadcrumb stack with:
 * - SessionStorage persistence
 * - URL encoding for sharing
 * - Max 10 items (FIFO)
 * - Navigation methods: push, pop, goToIndex, clear
 */

import { browser } from '$app/environment';

export interface BreadcrumbItem {
	provisionId: string;
	year: number;
	heading: string;
	timestamp: number;
}

class NavigationStore {
	breadcrumbs = $state<BreadcrumbItem[]>([]);
	readonly maxStackSize = 10;

	// Derived state
	canGoBack = $derived(this.breadcrumbs.length > 1);
	currentProvision = $derived(this.breadcrumbs[this.breadcrumbs.length - 1] ?? null);
	stackSize = $derived(this.breadcrumbs.length);

	constructor() {
		// Hydrate from sessionStorage on initialization
		if (browser) {
			this.hydrate();
		}
	}

	/**
	 * Push a new breadcrumb item to the stack.
	 * Enforces max stack size (FIFO).
	 */
	push(item: BreadcrumbItem): void {
		// Don't add duplicate if it's the same provision/year as current
		if (this.currentProvision?.provisionId === item.provisionId &&
		    this.currentProvision?.year === item.year) {
			return;
		}

		// Add timestamp if not provided
		const itemWithTimestamp = {
			...item,
			timestamp: item.timestamp || Date.now()
		};

		// Add to stack
		this.breadcrumbs = [...this.breadcrumbs, itemWithTimestamp];

		// Enforce max size (FIFO - remove oldest)
		if (this.breadcrumbs.length > this.maxStackSize) {
			this.breadcrumbs = this.breadcrumbs.slice(1);
		}

		this.persist();
	}

	/**
	 * Pop the last breadcrumb item from the stack.
	 * Returns the popped item or null if stack is empty.
	 */
	pop(): BreadcrumbItem | null {
		if (this.breadcrumbs.length === 0) {
			return null;
		}

		const popped = this.breadcrumbs[this.breadcrumbs.length - 1];
		this.breadcrumbs = this.breadcrumbs.slice(0, -1);
		this.persist();

		return popped;
	}

	/**
	 * Navigate to a specific index in the breadcrumb stack.
	 * Truncates the stack at that index (removes everything after).
	 */
	goToIndex(index: number): void {
		if (index < 0 || index >= this.breadcrumbs.length) {
			return;
		}

		// Truncate stack at index (keep items 0 to index inclusive)
		this.breadcrumbs = this.breadcrumbs.slice(0, index + 1);
		this.persist();
	}

	/**
	 * Clear the entire breadcrumb stack.
	 */
	clear(): void {
		this.breadcrumbs = [];
		this.persist();
	}

	/**
	 * Get breadcrumb item at a specific index.
	 */
	getAt(index: number): BreadcrumbItem | null {
		return this.breadcrumbs[index] ?? null;
	}

	/**
	 * Persist breadcrumbs to sessionStorage.
	 */
	private persist(): void {
		if (!browser) return;

		try {
			sessionStorage.setItem('navigation_breadcrumbs', JSON.stringify(this.breadcrumbs));
		} catch (error) {
			console.error('Failed to persist breadcrumbs:', error);
		}
	}

	/**
	 * Hydrate breadcrumbs from sessionStorage.
	 */
	private hydrate(): void {
		if (!browser) return;

		try {
			const stored = sessionStorage.getItem('navigation_breadcrumbs');
			if (stored) {
				const parsed = JSON.parse(stored) as BreadcrumbItem[];
				this.breadcrumbs = parsed;
			}
		} catch (error) {
			console.error('Failed to hydrate breadcrumbs:', error);
			this.breadcrumbs = [];
		}
	}

	/**
	 * Encode breadcrumbs to URL-safe string for sharing.
	 */
	encodeToUrl(): string {
		try {
			const encoded = btoa(JSON.stringify(this.breadcrumbs));
			return encoded;
		} catch (error) {
			console.error('Failed to encode breadcrumbs:', error);
			return '';
		}
	}

	/**
	 * Decode breadcrumbs from URL-safe string.
	 */
	decodeFromUrl(encoded: string): void {
		try {
			const decoded = atob(encoded);
			const parsed = JSON.parse(decoded) as BreadcrumbItem[];
			this.breadcrumbs = parsed.slice(0, this.maxStackSize); // Enforce max size
			this.persist();
		} catch (error) {
			console.error('Failed to decode breadcrumbs:', error);
		}
	}
}

// Export singleton instance
export const navigationStore = new NavigationStore();
