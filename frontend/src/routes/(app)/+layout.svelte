<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { theme } from '$lib/stores/theme.svelte';
	import { workspace } from '$lib/stores/workspace.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import BreadcrumbNav from '$lib/components/BreadcrumbNav.svelte';
	import ChatSidebar from '$lib/components/ChatSidebar.svelte';
	import KeyboardShortcutsHelp from '$lib/components/KeyboardShortcutsHelp.svelte';
	import { PanelRight, PanelRightClose, Share } from 'lucide-svelte';

	const navItems = [
		{ href: '/', label: 'Provisions' },
		{ href: '/timeline', label: 'Timeline' },
		{ href: '/compare', label: 'Compare' },
		{ href: '/graph', label: 'Graph' }
	];

	let showCommandPalette = $state(false);
	let showKeyboardHelp = $state(false);

	// Auth guard
	onMount(() => {
		if (!auth.loading && !auth.isAuthenticated) {
			goto('/login');
		}
	});

	function isActive(href: string, currentPath: string): boolean {
		if (href === '/') return currentPath === '/';
		return currentPath.startsWith(href);
	}

	// Handle global keyboard shortcuts
	function handleKeydown(e: KeyboardEvent) {
		// ⌘K or Ctrl+K to open command palette
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
			e.preventDefault();
			showCommandPalette = true;
		}

		// ⌘\ or Ctrl+\ to toggle sidebar
		if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
			e.preventDefault();
			workspace.toggleSidebar();
		}

		// ? to show keyboard shortcuts help
		if (e.key === '?' && !showCommandPalette && !workspace.state.sidebarOpen) {
			e.preventDefault();
			showKeyboardHelp = true;
		}

		// Escape to close sidebar (if open)
		if (e.key === 'Escape' && workspace.state.sidebarOpen) {
			e.preventDefault();
			workspace.toggleSidebar();
		}

		// Escape to close command palette (if open)
		if (e.key === 'Escape' && showCommandPalette) {
			e.preventDefault();
			showCommandPalette = false;
		}

		// Escape to close keyboard help (if open)
		if (e.key === 'Escape' && showKeyboardHelp) {
			e.preventDefault();
			showKeyboardHelp = false;
		}
	}

	// Handle share workspace state
	function handleShare() {
		try {
			const encoded = workspace.encodeToUrl();
			const shareUrl = `${window.location.origin}${window.location.pathname}?state=${encoded}`;

			navigator.clipboard.writeText(shareUrl);
			toasts.success('Workspace link copied to clipboard!');
		} catch (err) {
			toasts.error('Failed to copy link');
			console.error('Share error:', err);
		}
	}

	// Hydrate workspace from URL on mount
	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const encoded = params.get('state');

		if (encoded) {
			workspace.decodeFromUrl(encoded);
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
	<!-- Minimal Header -->
	<nav class="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
		<div class="max-w-full px-6">
			<div class="flex justify-between h-14">
				<!-- Logo & Navigation -->
				<div class="flex items-center gap-8">
					<a href="/" class="text-lg font-medium text-neutral-900 dark:text-neutral-50">
						Le Livre
					</a>
					<div class="flex gap-6">
						{#each navItems as item}
							{@const active = isActive(item.href, $page.url.pathname)}
							<a
								href={item.href}
								class="text-sm pb-[1px] border-b transition-colors {active
									? 'text-neutral-900 dark:text-neutral-50 border-primary'
									: 'text-neutral-500 dark:text-neutral-400 border-transparent hover:text-neutral-900 dark:hover:text-neutral-50'}"
							>
								{item.label}
							</a>
						{/each}
					</div>
				</div>

				<!-- User Menu, Search, Sidebar Toggle & Dark Mode Toggle -->
				<div class="flex items-center gap-2">
					<!-- User Menu (if authenticated) -->
					{#if auth.isAuthenticated}
						<div class="flex items-center gap-2 text-sm mr-2 px-3 py-1.5 rounded-md bg-neutral-100 dark:bg-neutral-800">
							<span class="text-neutral-600 dark:text-neutral-400">
								{auth.user?.email}
							</span>
							<button
								onclick={() => auth.logout()}
								class="text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
								title="Logout"
							>
								Logout
							</button>
						</div>
					{/if}

					<!-- Search Button -->
					<button
						onclick={() => (showCommandPalette = true)}
						class="flex items-center gap-2 px-3 py-1.5 text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md transition-colors"
						aria-label="Search"
					>
						<!-- Search icon -->
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							></path>
						</svg>
						<span class="hidden sm:inline">Search</span>
						<kbd class="hidden sm:inline-block px-1.5 py-0.5 text-xs bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-700">⌘K</kbd>
					</button>

					<!-- Sidebar Toggle Button -->
					<button
						onclick={() => workspace.toggleSidebar()}
						class="p-2 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
						aria-label="Toggle chat sidebar"
						title={workspace.state.sidebarOpen ? 'Close sidebar (⌘\\)' : 'Open sidebar (⌘\\)'}
					>
						{#if workspace.state.sidebarOpen}
							<PanelRightClose class="w-5 h-5" />
						{:else}
							<PanelRight class="w-5 h-5" />
						{/if}
					</button>

					<!-- Share Button -->
					<button
						onclick={handleShare}
						class="p-2 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
						aria-label="Share workspace"
						title="Share workspace link"
					>
						<Share class="w-5 h-5" />
					</button>

					<!-- Dark Mode Toggle -->
					<button
						onclick={() => theme.toggle()}
						class="p-2 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
						aria-label="Toggle dark mode"
					>
						{#if theme.theme === 'dark'}
							<!-- Sun icon -->
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
								></path>
							</svg>
						{:else}
							<!-- Moon icon -->
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
								></path>
							</svg>
						{/if}
					</button>

					<!-- Keyboard Shortcuts Help Button -->
					<button
						onclick={() => (showKeyboardHelp = true)}
						class="p-2 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
						aria-label="Keyboard shortcuts"
						title="Keyboard shortcuts (Press ?)"
					>
						<!-- Help icon -->
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					</button>
				</div>
			</div>
		</div>
	</nav>

	<!-- Breadcrumb Navigation -->
	<BreadcrumbNav />

	<!-- Main Content + Sidebar -->
	<div class="flex h-[calc(100vh-3.5rem)]">
		<!-- Main content -->
		<main class="flex-1 overflow-hidden">
			<slot />
		</main>

		<!-- Sidebar (conditionally rendered) -->
		{#if workspace.state.sidebarOpen}
			<aside
				class="w-96 border-l border-neutral-200 dark:border-neutral-800 lg:relative md:fixed md:inset-y-0 md:right-0 md:z-40"
			>
				<ChatSidebar />
			</aside>
		{/if}
	</div>

	<!-- Command Palette -->
	<CommandPalette open={showCommandPalette} onClose={() => (showCommandPalette = false)} />

	<!-- Keyboard Shortcuts Help -->
	{#if showKeyboardHelp}
		<KeyboardShortcutsHelp onClose={() => (showKeyboardHelp = false)} />
	{/if}
</div>
