<script lang="ts">
	import '../app.css';
	import { theme } from '$lib/stores/theme.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';
	import { onMount } from 'svelte';

	// Initialize theme on mount
	onMount(() => {
		// Theme is initialized in the store, just ensure it's loaded
		theme.theme; // Access to trigger reactivity
	});
</script>

<svelte:head>
	<title>Le Livre</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
	<slot />
</div>

<!-- Toast Notifications -->
<Toast />
