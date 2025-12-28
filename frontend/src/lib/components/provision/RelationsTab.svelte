<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Provision, ProvisionContext } from '$lib/api';

	interface Props {
		provision: Provision;
		context: ProvisionContext;
		selectedYear: number;
	}

	let { provision, context, selectedYear }: Props = $props();

	function viewProvision(provisionId: string) {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${selectedYear}`);
	}

	function truncateText(text: string | undefined | null, maxLength: number = 150): string {
		if (!text) return '';
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<div class="space-y-6">
	<!-- Parent -->
	{#if context.relations?.parent}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4 flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
				</svg>
				Parent Provision
			</h2>

			<button
				onclick={() => viewProvision(context.relations.parent.provision_id)}
				class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
			>
				<div class="flex items-start justify-between gap-4">
					<div class="flex-1">
						<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-2">
							{context.relations.parent.provision_id}
						</p>
						{#if context.relations.parent.heading}
							<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
								{context.relations.parent.heading}
							</p>
						{/if}
						<p class="text-sm text-neutral-600 dark:text-neutral-400">
							{truncateText(context.relations.parent.text_content)}
						</p>
					</div>
					<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
					</svg>
				</div>
			</button>
		</div>
	{/if}

	<!-- Children -->
	{#if context.relations?.children && context.relations.children.length > 0}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4 flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
				Child Provisions
				<span class="text-sm font-normal text-neutral-500 dark:text-neutral-400">
					({context.relations.children.length})
				</span>
			</h2>

			<div class="space-y-2">
				{#each context.relations.children as child}
					<button
						onclick={() => viewProvision(child.provision_id)}
						class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex-1">
								<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-2">
									{child.provision_id}
								</p>
								{#if child.heading}
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
										{child.heading}
									</p>
								{/if}
								<p class="text-sm text-neutral-600 dark:text-neutral-400">
									{truncateText(child.text_content)}
								</p>
							</div>
							<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- References (what this provision points to) -->
	{#if context.relations?.references && context.relations.references.length > 0}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4 flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
				</svg>
				References
				<span class="text-sm font-normal text-neutral-500 dark:text-neutral-400">
					({context.relations.references.length})
				</span>
			</h2>
			<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
				Provisions that this provision depends on
			</p>

			<div class="space-y-2">
				{#each context.relations.references as ref}
					<button
						onclick={() => viewProvision(ref.provision_id)}
						class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex-1">
								<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-2">
									{ref.provision_id}
								</p>
								{#if ref.heading}
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
										{ref.heading}
									</p>
								{/if}
								{#if ref.text_content}
									<p class="text-sm text-neutral-600 dark:text-neutral-400">
										{truncateText(ref.text_content)}
									</p>
								{/if}
							</div>
							<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Referenced By (what points to this provision) -->
	{#if context.relations?.referenced_by && context.relations.referenced_by.length > 0}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4 flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
				</svg>
				Referenced By
				<span class="text-sm font-normal text-neutral-500 dark:text-neutral-400">
					({context.relations.referenced_by.length})
				</span>
			</h2>
			<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
				Provisions that depend on this provision
			</p>

			<div class="space-y-2">
				{#each context.relations.referenced_by as ref}
					<button
						onclick={() => viewProvision(ref.provision_id)}
						class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex-1">
								<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-2">
									{ref.provision_id}
								</p>
								{#if ref.heading}
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
										{ref.heading}
									</p>
								{/if}
								{#if ref.text_content}
									<p class="text-sm text-neutral-600 dark:text-neutral-400">
										{truncateText(ref.text_content)}
									</p>
								{/if}
							</div>
							<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Semantically Similar -->
	{#if context.similar && context.similar.length > 0}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-4 flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
				</svg>
				Similar Provisions
				<span class="text-sm font-normal text-neutral-500 dark:text-neutral-400">
					({context.similar.length})
				</span>
			</h2>
			<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
				Semantically similar provisions based on content analysis
			</p>

			<div class="space-y-2">
				{#each context.similar as similar}
					<button
						onclick={() => viewProvision(similar.provision_id)}
						class="w-full text-left p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-sm transition-all"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex-1">
								<div class="flex items-center gap-2 mb-2">
									<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400">
										{similar.provision_id}
									</p>
									<span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
										{Math.round(similar.similarity_score * 100)}% similar
									</span>
								</div>
								{#if similar.heading}
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-1">
										{similar.heading}
									</p>
								{/if}
								<p class="text-sm text-neutral-600 dark:text-neutral-400">
									{truncateText(similar.text_content)}
								</p>
							</div>
							<svg class="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Empty state -->
	{#if !context.relations?.parent && (!context.relations?.children || context.relations.children.length === 0) && (!context.relations?.references || context.relations.references.length === 0) && (!context.relations?.referenced_by || context.relations.referenced_by.length === 0) && (!context.similar || context.similar.length === 0)}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-12 text-center">
			<svg class="w-12 h-12 mx-auto text-neutral-400 dark:text-neutral-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
			</svg>
			<p class="text-neutral-600 dark:text-neutral-400">
				No relationships found for this provision
			</p>
		</div>
	{/if}
</div>
