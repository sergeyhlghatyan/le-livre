import { apiCache } from '$lib/cache';

/**
 * Prefetch action parameters
 */
export interface PrefetchParams {
	provisionId: string;
	year: number;
	delay?: number; // Debounce delay in milliseconds (default 300ms)
}

/**
 * Svelte action for hover-triggered prefetching
 *
 * Usage:
 * ```svelte
 * <a use:prefetch={{ provisionId, year }}>Link</a>
 * ```
 *
 * Triggers prefetch after hovering for 300ms (debounced).
 * Cancels prefetch if mouse leaves before delay.
 */
export function prefetch(node: HTMLElement, params: PrefetchParams) {
	let timeoutId: ReturnType<typeof setTimeout> | null = null;

	function handleMouseEnter() {
		// Clear any existing timeout
		if (timeoutId !== null) {
			clearTimeout(timeoutId);
		}

		// Start debounce timer
		timeoutId = setTimeout(() => {
			apiCache.prefetchProvisionContext(params.provisionId, params.year);
		}, params.delay ?? 300);
	}

	function handleMouseLeave() {
		// Cancel prefetch if mouse leaves before delay
		if (timeoutId !== null) {
			clearTimeout(timeoutId);
			timeoutId = null;
		}
	}

	// Attach event listeners
	node.addEventListener('mouseenter', handleMouseEnter);
	node.addEventListener('mouseleave', handleMouseLeave);

	return {
		/**
		 * Update action parameters
		 */
		update(newParams: PrefetchParams) {
			params = newParams;
		},

		/**
		 * Cleanup on destroy
		 */
		destroy() {
			if (timeoutId !== null) {
				clearTimeout(timeoutId);
			}
			node.removeEventListener('mouseenter', handleMouseEnter);
			node.removeEventListener('mouseleave', handleMouseLeave);
		}
	};
}
