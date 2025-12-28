import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { toasts } from './toast.svelte';

export interface User {
	id: number;
	email: string;
	is_active: boolean;
	is_superuser: boolean;
}

class AuthStore {
	user = $state<User | null>(null);
	loading = $state(true);

	// Derived state
	isAuthenticated = $derived(this.user !== null);
	isAdmin = $derived(this.user?.is_superuser ?? false);

	constructor() {
		if (browser) {
			this.load();
			this.checkAuth();
		}
	}

	/**
	 * Login with email and password
	 */
	async login(email: string, password: string): Promise<void> {
		try {
			const user = await api.login(email, password);
			this.user = user;
			this.save();
			toasts.success('Logged in successfully!');
			goto('/');
		} catch (err) {
			toasts.error('Login failed: ' + (err as Error).message);
			throw err;
		}
	}

	/**
	 * Logout and clear session
	 */
	async logout(): Promise<void> {
		try {
			await api.logout();
			this.user = null;
			this.clear();
			toasts.success('Logged out successfully');
			goto('/login');
		} catch (err) {
			// Even if API call fails, clear local state
			this.user = null;
			this.clear();
			goto('/login');
		}
	}

	/**
	 * Check if user is authenticated by verifying token
	 */
	async checkAuth(): Promise<void> {
		this.loading = true;

		try {
			const user = await api.getMe();
			this.user = user;
			this.save();
		} catch (err) {
			// Token invalid or expired, clear state
			this.user = null;
			this.clear();
		} finally {
			this.loading = false;
		}
	}

	/**
	 * Refresh access token
	 */
	async refresh(): Promise<void> {
		try {
			await api.refreshToken();
			// Re-check auth after refresh
			await this.checkAuth();
		} catch (err) {
			// Refresh failed, clear state and redirect to login
			this.user = null;
			this.clear();
			goto('/login');
		}
	}

	/**
	 * Load user from localStorage
	 */
	private load(): void {
		if (!browser) return;

		try {
			const stored = localStorage.getItem('auth_user');
			if (stored) {
				this.user = JSON.parse(stored);
			}
		} catch (e) {
			console.error('Failed to load auth user:', e);
		}
	}

	/**
	 * Save user to localStorage
	 */
	private save(): void {
		if (!browser) return;

		try {
			if (this.user) {
				localStorage.setItem('auth_user', JSON.stringify(this.user));
			}
		} catch (e) {
			console.error('Failed to save auth user:', e);
		}
	}

	/**
	 * Clear user from localStorage
	 */
	private clear(): void {
		if (!browser) return;

		try {
			localStorage.removeItem('auth_user');
		} catch (e) {
			console.error('Failed to clear auth user:', e);
		}
	}
}

export const auth = new AuthStore();
