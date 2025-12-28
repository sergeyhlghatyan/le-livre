<script lang="ts">
	import { api, type GraphResponse } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import cytoscape, { type Core, type LayoutOptions } from 'cytoscape';
	import { goto } from '$app/navigation';
	import Breadcrumb, { type BreadcrumbItem } from '$lib/components/ui/Breadcrumb.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { onMount } from 'svelte';

	// Auth guard
	onMount(() => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
		}
	});

	let provisionId = $state('/us/usc/t18/s922/a');
	let year = $state(2024);
	let loading = $state(false);
	let error = $state('');
	let graphData = $state<GraphResponse | null>(null);
	let selectedNode = $state<string | null>(null);
	let layout = $state<'hierarchical' | 'force' | 'circular' | 'grid'>('hierarchical');

	let cyContainer = $state<HTMLDivElement>();
	let cy: Core | null = null;

	const breadcrumbItems = $derived<BreadcrumbItem[]>([
		{ label: 'Home', href: '/' },
		{ label: 'Graph', href: undefined },
		...(graphData ? [{ label: provisionId }] : [])
	]);

	// Initialize Cytoscape when both container and data are ready
	$effect(() => {
		if (graphData && cyContainer) {
			// Destroy existing instance
			if (cy) {
				cy.destroy();
			}

			// Initialize with current graphData
			initializeCytoscape(graphData);
		}
	});

	// Cleanup on unmount
	$effect(() => {
		return () => {
			if (cy) {
				cy.destroy();
				cy = null;
			}
		};
	});

	async function loadGraph() {
		if (!provisionId.trim()) return;

		loading = true;
		error = '';
		graphData = null;
		selectedNode = null;

		try {
			const data = await api.getGraph(provisionId, year);
			graphData = data; // $effect will handle initialization
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load graph';
		} finally {
			loading = false;
		}
	}

	function initializeCytoscape(data: GraphResponse) {
		if (!cyContainer) {
			console.error('Cytoscape container not available');
			return;
		}

		console.log('Initializing Cytoscape with', data.nodes.length, 'nodes');

		// Convert data to Cytoscape format
		const elements = [
			...data.nodes.map((node) => ({
				data: {
					id: node.id,
					label: node.label,
					level: node.level,
					heading: node.heading
				}
			})),
			...data.edges.map((edge) => ({
				data: {
					id: `${edge.source}-${edge.target}`,
					source: edge.source,
					target: edge.target,
					type: edge.type,
					display_text: edge.display_text
				}
			}))
		];

		cy = cytoscape({
			container: cyContainer,
			elements,
			style: [
				{
					selector: 'node',
					style: {
						'background-color': '#FFFFFF',
						'border-width': 1,
						'border-color': '#E5E5E5',
						label: 'data(label)',
						'font-family': 'JetBrains Mono, monospace',
						'font-size': '11px',
						color: '#171717',
						'text-halign': 'center',
						'text-valign': 'center',
						width: 80,
						height: 40,
						shape: 'roundrectangle'
					}
				},
				{
					selector: 'node:selected',
					style: {
						'border-color': '#2563EB',
						'border-width': 2
					}
				},
				{
					selector: 'edge',
					style: {
						width: 1,
						'line-color': '#D4D4D4',
						'target-arrow-color': '#D4D4D4',
						'target-arrow-shape': 'triangle',
						'curve-style': 'bezier',
						'font-size': '9px',
						'font-family': 'JetBrains Mono, monospace',
						color: '#737373'
					}
				},
				{
					selector: 'edge[type="references"]',
					style: {
						'line-style': 'dashed'
					}
				}
			],
			layout: getLayoutOptions(layout),
			minZoom: 0.5,
			maxZoom: 2,
			wheelSensitivity: 0.2
		});

		// Handle node click - navigate to provision view
		cy.on('tap', 'node', (evt) => {
			const node = evt.target;
			const nodeId = node.id();
			// Navigate immediately to provision view
			goto(`/provision/${encodeURIComponent(nodeId)}?year=${year}`);
		});

		// Handle canvas click (deselect)
		cy.on('tap', (evt) => {
			if (evt.target === cy) {
				selectedNode = null;
			}
		});
	}

	function getLayoutOptions(layoutType: typeof layout): LayoutOptions {
		const layouts: Record<typeof layout, LayoutOptions> = {
			hierarchical: {
				name: 'breadthfirst',
				directed: true,
				spacingFactor: 1.5,
				padding: 30
			},
			force: {
				name: 'cose',
				padding: 30,
				nodeRepulsion: 8000,
				idealEdgeLength: 100,
				edgeElasticity: 100
			},
			circular: {
				name: 'circle',
				padding: 30,
				spacingFactor: 1.5
			},
			grid: {
				name: 'grid',
				padding: 30,
				spacingFactor: 1.5
			}
		};

		return layouts[layoutType];
	}

	function changeLayout(newLayout: typeof layout) {
		layout = newLayout;
		if (cy) {
			cy.layout(getLayoutOptions(newLayout)).run();
		}
	}

	function resetZoom() {
		if (cy) {
			cy.fit(undefined, 30);
		}
	}

	function exportPNG() {
		if (cy) {
			const png = cy.png({ scale: 2, full: true });
			const link = document.createElement('a');
			link.download = `${provisionId.replace(/\//g, '-')}-graph.png`;
			link.href = png;
			link.click();
		}
	}

	// Get selected node data
	const selectedNodeData = $derived.by(() => {
		if (!selectedNode || !graphData) return null;
		return graphData.nodes.find((n) => n.id === selectedNode);
	});
</script>

<div class="flex flex-col h-full">
	<!-- Header -->
	<div
		class="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-6 py-3"
	>
		<Breadcrumb items={breadcrumbItems} />
		<div class="flex items-center justify-between mt-3">
			<div class="flex items-center gap-4">
				<h1 class="text-lg font-medium text-neutral-900 dark:text-neutral-50">
					{#if graphData}
						Graph: {provisionId}
					{:else}
						Reference Graph
					{/if}
				</h1>
			</div>

			{#if graphData}
				<div class="flex items-center gap-2">
					<!-- Layout Dropdown -->
					<select
						bind:value={layout}
						onchange={() => changeLayout(layout)}
						class="px-3 py-1.5 text-xs border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors"
					>
						<option value="hierarchical">Hierarchical</option>
						<option value="force">Force-Directed</option>
						<option value="circular">Circular</option>
						<option value="grid">Grid</option>
					</select>

					<!-- Controls -->
					<Button variant="ghost" onclick={resetZoom}>Reset Zoom</Button>
					<Button variant="ghost" onclick={exportPNG}>Export PNG</Button>
				</div>
			{/if}
		</div>
	</div>

	{#if !graphData}
		<!-- Input Form -->
		<div class="flex-1 overflow-y-auto px-6 py-8">
			<div class="max-w-2xl mx-auto">
				<form
					onsubmit={(e) => {
						e.preventDefault();
						loadGraph();
					}}
					class="space-y-4"
				>
					<div>
						<label for="provision-id" class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
							Provision ID
						</label>
						<Input id="provision-id" bind:value={provisionId} placeholder="/us/usc/t18/s922/a" />
					</div>

					<div>
						<label for="year" class="block text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
							Year
						</label>
						<Input id="year" type="number" bind:value={year} />
					</div>

					<Button type="submit" variant="primary" disabled={loading || !provisionId.trim()}>
						{loading ? 'Loading...' : 'Load Graph'}
					</Button>
				</form>

				{#if error}
					<div
						class="mt-6 p-4 border border-error rounded-lg bg-white dark:bg-neutral-950 text-error text-sm"
					>
						{error}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<!-- Graph View -->
		<div class="flex-1 relative overflow-hidden">
			<!-- Cytoscape Container -->
			<div bind:this={cyContainer} class="absolute inset-0 bg-white dark:bg-neutral-950"></div>
		</div>
	{/if}
</div>
