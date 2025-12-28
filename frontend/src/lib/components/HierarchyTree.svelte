<script lang="ts">
	import type { HierarchyNode } from '$lib/api';
	import InlineDiff from './InlineDiff.svelte';

	interface Props {
		node: HierarchyNode;
		granularity?: 'word' | 'sentence';
		depth?: number;
	}

	let { node, granularity = $bindable('sentence'), depth = 0 }: Props = $props();

	let expanded = $state(true);

	// Auto-expand changed branches
	$effect(() => {
		if (node.status === 'modified' || node.children.some((c) => c.status !== 'unchanged')) {
			expanded = true;
		}
	});

	function toggleExpand() {
		expanded = !expanded;
	}

	function getStatusIcon(status: string): string {
		switch (status) {
			case 'modified':
				return '🔴';
			case 'added':
				return '➕';
			case 'removed':
				return '➖';
			case 'unchanged':
				return '✅';
			default:
				return '⚪';
		}
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'modified':
				return 'text-red-700 bg-red-50';
			case 'added':
				return 'text-green-700 bg-green-50';
			case 'removed':
				return 'text-gray-700 bg-gray-50';
			case 'unchanged':
				return 'text-gray-600 bg-gray-50';
			default:
				return 'text-gray-600 bg-gray-50';
		}
	}

	const hasChildren = $derived(node.children && node.children.length > 0);
</script>

<div class="hierarchy-node" style="margin-left: {depth * 1.5}rem;">
	<!-- Node Header -->
	<div class="node-header {getStatusColor(node.status)}">
		<button onclick={toggleExpand} class="expand-button" disabled={!hasChildren}>
			{#if hasChildren}
				<span class="expand-icon">{expanded ? '▼' : '▶'}</span>
			{:else}
				<span class="expand-icon invisible">▶</span>
			{/if}
		</button>

		<span class="status-icon">{getStatusIcon(node.status)}</span>

		<div class="node-info">
			<span class="provision-num font-semibold">{node.provision_num}</span>
			<span class="provision-level text-xs uppercase opacity-75">{node.provision_level}</span>
			{#if node.heading}
				<span class="heading text-sm font-medium">{node.heading}</span>
			{/if}
		</div>
	</div>

	<!-- Expanded Content -->
	{#if expanded}
		<!-- Show diff if text changed -->
		{#if node.text_changed && node.inline_diff}
			<div class="diff-content">
				<div class="diff-label">Changes:</div>
				<InlineDiff parts={node.inline_diff[granularity]} />
			</div>
		{/if}

		<!-- Recursively render children -->
		{#if hasChildren}
			<div class="children">
				{#each node.children as child}
					<svelte:self node={child} {granularity} depth={depth + 1} />
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.hierarchy-node {
		margin-bottom: 0.5rem;
	}

	.node-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		border-radius: 0.375rem;
		border: 1px solid rgba(0, 0, 0, 0.1);
		cursor: pointer;
		transition: all 0.2s;
	}

	.node-header:hover {
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.expand-button {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 1.25rem;
		height: 1.25rem;
	}

	.expand-button:disabled {
		cursor: default;
	}

	.expand-icon {
		font-size: 0.75rem;
		line-height: 1;
	}

	.status-icon {
		font-size: 1rem;
		line-height: 1;
	}

	.node-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex: 1;
	}

	.provision-num {
		min-width: 3rem;
	}

	.diff-content {
		margin-top: 0.75rem;
		margin-left: 2.75rem;
		padding: 0.75rem;
		background-color: #f9fafb;
		border-left: 3px solid #3b82f6;
		border-radius: 0.25rem;
	}

	.diff-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: #6b7280;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.children {
		margin-top: 0.5rem;
	}
</style>
