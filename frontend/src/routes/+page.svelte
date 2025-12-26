<script lang="ts">
	import { api, type ChatResponse } from '$lib/api';

	let query = $state('');
	let loading = $state(false);
	let response = $state<ChatResponse | null>(null);
	let error = $state('');

	const exampleQuestions = [
		"What are the requirements for licensed firearms dealers?",
		"What provisions apply to interstate firearm transfers?",
		"What are the prohibited acts under section 922?",
		"How have ammunition regulations changed over time?",
		"What are the penalties for violating section 922?"
	];

	function setExample(example: string) {
		query = example;
	}

	async function handleSubmit() {
		if (!query.trim()) return;

		loading = true;
		error = '';
		response = null;

		try {
			response = await api.chat({ query, limit: 10 });
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			loading = false;
		}
	}
</script>

<div class="px-4 py-6">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-2">Legal Assistant</h1>
		<p class="text-gray-600">Ask questions about US firearms law (Title 18 USC)</p>
	</div>

	<!-- Example Questions -->
	{#if !response}
		<div class="mb-6">
			<p class="text-sm font-medium text-gray-700 mb-3">Try these examples:</p>
			<div class="flex flex-wrap gap-2">
				{#each exampleQuestions as example}
					<button
						onclick={() => setExample(example)}
						class="px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-sm rounded-lg border border-blue-200 transition-colors"
					>
						{example}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Chat Input -->
	<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
			<label for="query" class="block text-sm font-medium text-gray-700 mb-2">
				Your Question
			</label>
			<textarea
				id="query"
				bind:value={query}
				rows="3"
				class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
				placeholder="e.g., What are the requirements for licensed firearms dealers?"
			></textarea>
			<div class="mt-4">
				<button
					type="submit"
					disabled={loading || !query.trim()}
					class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
				>
					{loading ? 'Searching...' : 'Ask Question'}
				</button>
			</div>
		</form>
	</div>

	<!-- Error Message -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
			<p class="text-red-800">{error}</p>
		</div>
	{/if}

	<!-- Response -->
	{#if response}
		<div class="space-y-6">
			<!-- Answer -->
			<div class="bg-white rounded-lg shadow-sm border p-6">
				<h2 class="text-lg font-semibold text-gray-900 mb-4">Answer</h2>
				<div class="prose max-w-none text-gray-700 whitespace-pre-wrap">
					{response.answer}
				</div>
			</div>

			<!-- Search Stats -->
			<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
				<div class="flex gap-6 text-sm">
					<div>
						<span class="font-medium text-blue-900">Semantic Results:</span>
						<span class="text-blue-700 ml-2">{response.semantic_count}</span>
					</div>
					<div>
						<span class="font-medium text-blue-900">Graph Results:</span>
						<span class="text-blue-700 ml-2">{response.graph_count}</span>
					</div>
					<div>
						<span class="font-medium text-blue-900">Total Sources:</span>
						<span class="text-blue-700 ml-2">{response.sources.length}</span>
					</div>
				</div>
			</div>

			<!-- Sources -->
			<div class="bg-white rounded-lg shadow-sm border p-6">
				<h2 class="text-lg font-semibold text-gray-900 mb-4">Sources</h2>
				<div class="space-y-4">
					{#each response.sources as source, i}
						<div class="border-l-4 {source.source === 'semantic' ? 'border-blue-500' : 'border-green-500'} pl-4 py-2">
							<div class="flex items-center gap-2 mb-2">
								<span class="text-xs font-semibold uppercase px-2 py-1 rounded {source.source === 'semantic' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}">
									{source.source}
								</span>
								<span class="text-sm font-medium text-gray-900">
									{source.heading || source.provision_id}
								</span>
								<span class="text-sm text-gray-500">
									({source.year})
								</span>
								{#if source.similarity}
									<span class="text-xs text-gray-500 ml-auto">
										{(source.similarity * 100).toFixed(1)}% match
									</span>
								{/if}
							</div>
							<p class="text-sm text-gray-700">{source.text_content.substring(0, 300)}...</p>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
