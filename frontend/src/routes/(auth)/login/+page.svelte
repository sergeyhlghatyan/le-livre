<script lang="ts">
	import { auth } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	let email = $state('');
	let password = $state('');
	let isLoading = $state(false);
	let error = $state('');

	// Redirect if already authenticated
	onMount(() => {
		if (auth.isAuthenticated) {
			goto('/');
		}
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';

		if (!email || !password) {
			error = 'Please enter both email and password';
			return;
		}

		isLoading = true;

		try {
			await auth.login(email, password);
			// auth.login handles redirect to home page
		} catch (err) {
			error = (err as Error).message || 'Login failed. Please check your credentials.';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="w-full max-w-md">
	<Card>
			<!-- Logo and Title -->
			<div class="text-center mb-8">
				<h1 class="text-2xl font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
					Le Livre
				</h1>
				<p class="text-sm text-neutral-500 dark:text-neutral-400">
					Sign in to access the legislative tracker
				</p>
			</div>

			<!-- Login Form -->
			<form onsubmit={handleSubmit} class="space-y-4">
				<!-- Email Input -->
				<div>
					<label for="email" class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
						Email
					</label>
					<Input
						id="email"
						type="email"
						placeholder="admin@example.com"
						bind:value={email}
						disabled={isLoading}
						required
					/>
				</div>

				<!-- Password Input -->
				<div>
					<label for="password" class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
						Password
					</label>
					<Input
						id="password"
						type="password"
						placeholder="Enter your password"
						bind:value={password}
						disabled={isLoading}
						required
					/>
				</div>

				<!-- Error Message -->
				{#if error}
					<div class="p-3 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
						<p class="text-sm text-red-600 dark:text-red-400">
							{error}
						</p>
					</div>
				{/if}

				<!-- Submit Button -->
				<Button
					type="submit"
					variant="primary"
					disabled={isLoading}
					class="w-full"
				>
					{isLoading ? 'Signing in...' : 'Sign In'}
				</Button>
			</form>

			<!-- Admin Only Notice -->
			<div class="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-800">
				<p class="text-xs text-center text-neutral-500 dark:text-neutral-400">
					Access is restricted to authorized users only.
					<br/>
					Contact your administrator for account access.
				</p>
			</div>
	</Card>
</div>
