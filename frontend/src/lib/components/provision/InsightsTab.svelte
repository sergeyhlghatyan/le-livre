<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Provision, ProvisionContext } from '$lib/api';

	interface Props {
		provision: Provision;
		context: ProvisionContext;
	}

	let { provision, context }: Props = $props();

	// Calculate importance score based on available data
	function calculateImportanceScore(): number {
		let score = 50; // Base score

		// Increase score based on references
		if (context.relations?.referenced_by) {
			score += Math.min(context.relations.referenced_by.length * 5, 30);
		}

		// Increase score based on children
		if (context.relations?.children) {
			score += Math.min(context.relations.children.length * 2, 15);
		}

		// Increase score based on amendments
		if (context.amendments && context.amendments.length > 0) {
			score += Math.min(context.amendments.length * 3, 10);
		}

		return Math.min(score, 100);
	}

	function getImportanceLabel(score: number): string {
		if (score >= 80) return 'Very High';
		if (score >= 60) return 'High';
		if (score >= 40) return 'Medium';
		if (score >= 20) return 'Low';
		return 'Very Low';
	}

	function getImportanceColor(score: number): string {
		if (score >= 80) return 'text-red-600 dark:text-red-400';
		if (score >= 60) return 'text-amber-600 dark:text-amber-400';
		if (score >= 40) return 'text-blue-600 dark:text-blue-400';
		return 'text-neutral-600 dark:text-neutral-400';
	}

	function viewProvision(provisionId: string, year: number = 2024) {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${year}`);
	}

	const importanceScore = calculateImportanceScore();
</script>

<div class="space-y-6">
	<!-- Importance Score -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-6">
			Provision Importance
		</h2>

		<div class="flex items-center gap-6">
			<!-- Score circle -->
			<div class="relative w-32 h-32">
				<svg class="w-full h-full transform -rotate-90">
					<circle
						cx="64"
						cy="64"
						r="56"
						class="stroke-neutral-200 dark:stroke-neutral-700"
						fill="none"
						stroke-width="8"
					/>
					<circle
						cx="64"
						cy="64"
						r="56"
						class="stroke-blue-600 transition-all"
						fill="none"
						stroke-width="8"
						stroke-dasharray={`${2 * Math.PI * 56}`}
						stroke-dashoffset={`${2 * Math.PI * 56 * (1 - importanceScore / 100)}`}
						stroke-linecap="round"
					/>
				</svg>
				<div class="absolute inset-0 flex items-center justify-center">
					<span class="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
						{importanceScore}
					</span>
				</div>
			</div>

			<!-- Score details -->
			<div class="flex-1">
				<p class="text-2xl font-bold {getImportanceColor(importanceScore)} mb-2">
					{getImportanceLabel(importanceScore)} Importance
				</p>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					This provision ranks in the {getImportanceLabel(importanceScore).toLowerCase()} importance category based on its relationships, references, and change history.
				</p>
			</div>
		</div>
	</div>

	<!-- Key Statistics -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
			Key Statistics
		</h3>

		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
				<p class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">References</p>
				<p class="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
					{context.relations?.references?.length || 0}
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
				<p class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">Referenced By</p>
				<p class="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
					{context.relations?.referenced_by?.length || 0}
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
				<p class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">Children</p>
				<p class="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
					{context.relations?.children?.length || 0}
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded">
				<p class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">Amendments</p>
				<p class="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
					{context.amendments?.length || 0}
				</p>
			</div>
		</div>
	</div>

	<!-- Definitions -->
	{#if context.definitions && (context.definitions.provides.length > 0 || context.definitions.uses.length > 0)}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
				Definitions
			</h3>

			{#if context.definitions.provides.length > 0}
				<div class="mb-6">
					<h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
						Provides Definitions ({context.definitions.provides.length})
					</h4>
					<div class="flex flex-wrap gap-2">
						{#each context.definitions.provides as def}
							<span class="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded-full text-sm">
								{def.term}
								{#if def.usage_count}
									<span class="ml-1 text-xs opacity-75">({def.usage_count} uses)</span>
								{/if}
							</span>
						{/each}
					</div>
				</div>
			{/if}

			{#if context.definitions.uses.length > 0}
				<div>
					<h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
						Uses Definitions ({context.definitions.uses.length})
					</h4>
					<div class="space-y-2">
						{#each context.definitions.uses as use}
							<div class="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900 rounded">
								<div class="flex items-center gap-3">
									<span class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
										{use.term}
									</span>
									<span class="text-xs text-neutral-500 dark:text-neutral-400">
										{use.confidence ? Math.round(use.confidence * 100) + '% confidence' : ''}
									</span>
								</div>
								<button
									onclick={() => viewProvision(use.definition_id)}
									class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
								>
									View definition →
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Common patterns -->
	<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
		<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
			Common Questions
		</h3>

		<div class="space-y-3">
			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
				<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
					What does this provision regulate?
				</p>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					This provision is part of {provision.section_num && `Title 18 USC § ${provision.section_num}`},
					governing {provision.heading?.toLowerCase() || 'specific regulations'}.
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
				<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
					When was it last changed?
				</p>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					{#if context.amendments && context.amendments.length > 0}
						Last changed in {Math.max(...context.amendments.map(a => a.year_new))}.
					{:else}
						No recent amendments recorded.
					{/if}
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
				<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
					What provisions depend on this?
				</p>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					{context.relations?.referenced_by?.length || 0} other provision{context.relations?.referenced_by?.length !== 1 ? 's' : ''} reference{context.relations?.referenced_by?.length === 1 ? 's' : ''} this provision.
				</p>
			</div>

			<div class="p-4 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
				<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
					Are there related provisions?
				</p>
				<p class="text-sm text-neutral-600 dark:text-neutral-400">
					{#if context.similar && context.similar.length > 0}
						Yes, {context.similar.length} semantically similar provision{context.similar.length > 1 ? 's' : ''} found.
					{:else}
						No semantically similar provisions identified.
					{/if}
				</p>
			</div>
		</div>
	</div>

	<!-- Frequently viewed with -->
	{#if context.similar && context.similar.length > 0}
		<div class="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
			<h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-50 mb-4">
				Frequently Viewed With
			</h3>
			<p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
				Provisions with similar content
			</p>

			<div class="space-y-2">
				{#each context.similar.slice(0, 5) as similar}
					<button
						onclick={() => viewProvision(similar.provision_id)}
						class="w-full text-left p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
					>
						<div class="flex items-center justify-between">
							<div class="flex-1">
								<p class="text-xs font-mono text-neutral-500 dark:text-neutral-400 mb-1">
									{similar.provision_id}
								</p>
								{#if similar.heading}
									<p class="text-sm font-medium text-neutral-900 dark:text-neutral-50">
										{similar.heading}
									</p>
								{/if}
							</div>
							<span class="ml-3 px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded text-xs">
								{Math.round(similar.similarity_score * 100)}% match
							</span>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
