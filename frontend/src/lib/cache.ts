import { api } from './api';
import type { Provision, GraphResponse, TimelineChange, ProvisionContext } from './api';

/**
 * Cache entry with data and expiration
 */
interface CacheEntry<T> {
	data: T;
	timestamp: number;
	expiresAt: number;
}

/**
 * LRU Cache with TTL for API responses
 *
 * Features:
 * - Max 100 entries (LRU eviction when full)
 * - Default 5 minute TTL
 * - Automatic expiration checking
 * - Prefetch support for provision context
 */
class ApiCache {
	private cache = new Map<string, CacheEntry<any>>();
	private maxSize = 100; // Max 100 entries
	private defaultTTL = 5 * 60 * 1000; // 5 minutes

	/**
	 * Get cached data if available and not expired
	 */
	get<T>(key: string): T | null {
		const entry = this.cache.get(key);

		if (!entry) return null;

		// Check expiration
		if (Date.now() > entry.expiresAt) {
			this.cache.delete(key);
			return null;
		}

		// Move to end (LRU)
		this.cache.delete(key);
		this.cache.set(key, entry);

		return entry.data as T;
	}

	/**
	 * Set cached data with optional TTL
	 */
	set<T>(key: string, data: T, ttl: number = this.defaultTTL): void {
		// Enforce max size (LRU eviction)
		if (this.cache.size >= this.maxSize) {
			const oldestKey = this.cache.keys().next().value;
			if (oldestKey) {
				this.cache.delete(oldestKey);
			}
		}

		this.cache.set(key, {
			data,
			timestamp: Date.now(),
			expiresAt: Date.now() + ttl
		});
	}

	/**
	 * Check if key exists and is not expired
	 */
	has(key: string): boolean {
		return this.get(key) !== null;
	}

	/**
	 * Invalidate cache entries matching a pattern
	 */
	invalidate(pattern: RegExp): void {
		for (const key of this.cache.keys()) {
			if (pattern.test(key)) {
				this.cache.delete(key);
			}
		}
	}

	/**
	 * Clear all cache entries
	 */
	clear(): void {
		this.cache.clear();
	}

	/**
	 * Prefetch provision context data in the background
	 *
	 * Fetches graph relationships and timeline changes for a provision
	 * to make navigation feel instant. Silent fails if requests error.
	 */
	prefetchProvisionContext(provisionId: string, year: number): void {
		// Prefetch graph relationships
		const graphKey = `graph:${provisionId}:${year}`;
		if (!this.has(graphKey)) {
			api
				.getGraph(provisionId, year)
				.then((data) => this.set(graphKey, data))
				.catch(() => {}); // Silent fail
		}

		// Prefetch timeline changes
		const timelineKey = `timeline:${provisionId}`;
		if (!this.has(timelineKey)) {
			api
				.getProvisionTimelineChanges(provisionId)
				.then((data) => this.set(timelineKey, data))
				.catch(() => {}); // Silent fail
		}
	}

	/**
	 * Get cache statistics
	 */
	getStats() {
		return {
			size: this.cache.size,
			maxSize: this.maxSize,
			entries: Array.from(this.cache.keys())
		};
	}
}

// Singleton instance
export const apiCache = new ApiCache();

/**
 * Cached API wrapper - wraps GET endpoints with cache layer
 */
export const cachedApi = {
	/**
	 * Get provision with caching
	 */
	async getProvision(provisionId: string, year: number): Promise<Provision> {
		const cacheKey = `provision:${provisionId}:${year}`;
		const cached = apiCache.get<Provision>(cacheKey);

		if (cached) return cached;

		const data = await api.getProvision(provisionId, year);
		apiCache.set(cacheKey, data);
		return data;
	},

	/**
	 * Get graph relationships with caching
	 */
	async getGraph(provisionId: string, year: number): Promise<GraphResponse> {
		const cacheKey = `graph:${provisionId}:${year}`;
		const cached = apiCache.get<GraphResponse>(cacheKey);

		if (cached) return cached;

		const data = await api.getGraph(provisionId, year);
		apiCache.set(cacheKey, data);
		return data;
	},

	/**
	 * Get provision timeline changes with caching
	 */
	async getProvisionTimelineChanges(provisionId: string): Promise<TimelineChange[]> {
		const cacheKey = `timeline:${provisionId}`;
		const cached = apiCache.get<TimelineChange[]>(cacheKey);

		if (cached) return cached;

		const data = await api.getProvisionTimelineChanges(provisionId);
		apiCache.set(cacheKey, data);
		return data;
	},

	/**
	 * Get provision preview with caching
	 */
	async getProvisionPreview(
		provisionId: string,
		year: number
	): Promise<{ heading: string; text_content: string }> {
		const cacheKey = `preview:${provisionId}:${year}`;
		const cached = apiCache.get<{ heading: string; text_content: string }>(cacheKey);

		if (cached) return cached;

		const data = await api.getProvisionPreview(provisionId, year);
		apiCache.set(cacheKey, data);
		return data;
	},

	/**
	 * Get provision context with caching (5-minute TTL)
	 */
	async getProvisionContext(provisionId: string, year: number): Promise<ProvisionContext> {
		const cacheKey = `context:${provisionId}:${year}`;
		const cached = apiCache.get<ProvisionContext>(cacheKey);

		if (cached) return cached;

		const data = await api.getProvisionContext(provisionId, year);
		apiCache.set(cacheKey, data);
		return data;
	},

	// POST requests bypass cache (no caching for mutations)
	chat: api.chat,
	compareProvisions: api.compareProvisions,
	compareHierarchical: api.compareHierarchical,
	getTimeline: api.getTimeline,
	getProvisions: api.getProvisions
};
