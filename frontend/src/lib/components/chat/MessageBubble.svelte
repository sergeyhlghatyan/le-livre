<script lang="ts">
	import { marked } from 'marked';
	import type { Message } from '$lib/stores/chat.svelte';
	import SourceCard from './SourceCard.svelte';
	import SourceGroup from './SourceGroup.svelte';

	interface Props {
		message: Message;
	}

	let { message }: Props = $props();

	let copied = $state(false);

	// Configure marked for safe markdown rendering
	marked.setOptions({
		breaks: true,
		gfm: true
	});

	// Render markdown for assistant messages
	const renderedContent = $derived(() => {
		if (message.type === 'assistant' && !message.loading) {
			return marked.parse(message.content);
		}
		return message.content;
	});

	function copyToClipboard() {
		navigator.clipboard.writeText(message.content);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	function formatTime(date: Date): string {
		return new Intl.DateTimeFormat('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		}).format(date);
	}
</script>

<div class="flex flex-col gap-3 max-w-chat mx-auto">
	<!-- Metadata header for assistant messages (year used and source counts) -->
	{#if message.type === 'assistant' && message.response && !message.loading}
		<div class="flex items-center gap-3 px-4 text-xs text-neutral-500 dark:text-neutral-400">
			<span class="font-medium">Using {message.response.year_used || 2024} provisions</span>
			<span>•</span>
			<span>{message.response.semantic_count} semantic</span>
			<span>•</span>
			<span>{message.response.graph_count} graph</span>
		</div>
	{/if}

	<!-- Message -->
	<div class={message.type === 'user' ? 'flex justify-end' : 'flex justify-start'}>
		<div
			class={message.type === 'user'
				? 'bg-neutral-100 dark:bg-neutral-900 px-4 py-2.5 rounded-lg max-w-xl'
				: 'text-neutral-900 dark:text-neutral-50 px-4 py-2.5 max-w-full'}
		>
			{#if message.loading}
				<div class="flex gap-1 items-center">
					<div class="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse"></div>
					<div
						class="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse"
						style="animation-delay: 0.2s"
					></div>
					<div
						class="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse"
						style="animation-delay: 0.4s"
					></div>
				</div>
			{:else if message.type === 'assistant'}
				<!-- Render markdown for assistant messages -->
				<div class="prose prose-sm dark:prose-invert max-w-none">
					{@html renderedContent()}
				</div>
			{:else}
				<!-- Plain text for user messages -->
				<p class="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
			{/if}
		</div>
	</div>

	<!-- Timestamp & Actions -->
	{#if !message.loading}
		<div class={message.type === 'user' ? 'flex justify-end' : 'flex justify-start'}>
			<div class="flex items-center gap-3 px-4 text-xs text-neutral-500 dark:text-neutral-400">
				<span>{formatTime(message.timestamp)}</span>
				{#if message.type === 'assistant'}
					<button
						onclick={copyToClipboard}
						class="hover:text-neutral-900 dark:hover:text-neutral-50 transition-colors"
					>
						{copied ? 'Copied' : 'Copy'}
					</button>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Sources (for assistant messages) -->
	{#if message.type === 'assistant' && message.response && !message.loading}
		{#if message.response.sources.length > 0}
			{@const semanticSources = message.response.sources.filter(s => s.found_via?.includes('semantic') || s.source === 'semantic')}
			{@const graphSources = message.response.sources.filter(s => s.found_via?.includes('graph') || s.source === 'graph')}
			{@const bothSources = message.response.sources.filter(s => s.found_via && s.found_via.length > 1)}

			<!-- Grouped Source Display -->
			<div class="space-y-4">
				{#if semanticSources.length > 0}
					<SourceGroup
						title="Semantic Search"
						sources={semanticSources}
						variant="semantic"
						defaultExpanded={true}
					/>
				{/if}

				{#if graphSources.length > 0}
					<SourceGroup
						title="Graph Relationships"
						sources={graphSources}
						variant="graph"
						defaultExpanded={graphSources.length <= 3}
					/>
				{/if}

				{#if bothSources.length > 0}
					<SourceGroup
						title="Both Semantic & Graph"
						sources={bothSources}
						variant="both"
						defaultExpanded={true}
					/>
				{/if}
			</div>
		{/if}
	{/if}
</div>
