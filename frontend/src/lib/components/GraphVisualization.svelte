<script lang="ts">
	import { onMount } from 'svelte';
	import cytoscape from 'cytoscape';
	import type { GraphResponse } from '$lib/api';

	interface Props {
		graph: GraphResponse;
		centerNode: string;
	}

	let { graph, centerNode }: Props = $props();
	let container: HTMLDivElement;
	let cy: any;

	onMount(() => {
		if (!container || !graph) return;

		// Convert graph data to Cytoscape format
		const elements = [
			...graph.nodes.map(n => ({
				data: {
					id: n.id,
					label: n.label,
					level: n.level,
					heading: n.heading
				}
			})),
			...graph.edges.map(e => ({
				data: {
					id: `${e.source}-${e.target}`,
					source: e.source,
					target: e.target,
					label: e.type,
					edgeType: e.type
				}
			}))
		];

		// Initialize Cytoscape
		cy = cytoscape({
			container: container,
			elements: elements,
			style: [
				{
					selector: 'node',
					style: {
						'label': 'data(label)',
						'background-color': '#4F46E5',
						'color': '#fff',
						'text-valign': 'center',
						'text-halign': 'center',
						'font-size': '12px',
						'width': '60px',
						'height': '60px',
						'text-wrap': 'wrap',
						'text-max-width': '80px'
					}
				},
				{
					selector: `node[id="${centerNode}"]`,
					style: {
						'background-color': '#DC2626',
						'border-width': 3,
						'border-color': '#991B1B'
					}
				},
				{
					selector: 'edge',
					style: {
						'width': 2,
						'line-color': '#94A3B8',
						'target-arrow-color': '#94A3B8',
						'target-arrow-shape': 'triangle',
						'curve-style': 'bezier',
						'label': 'data(label)',
						'font-size': '10px',
						'text-rotation': 'autorotate',
						'text-margin-y': -10
					}
				},
				{
					selector: 'edge[edgeType="parent_of"]',
					style: {
						'line-color': '#6366F1',
						'target-arrow-color': '#6366F1'
					}
				},
				{
					selector: 'edge[edgeType="references"]',
					style: {
						'line-color': '#8B5CF6',
						'target-arrow-color': '#8B5CF6',
						'line-style': 'dashed'
					}
				}
			],
			layout: {
				name: 'cose',
				animate: false,
				idealEdgeLength: 100,
				nodeOverlap: 20,
				refresh: 20,
				fit: true,
				padding: 30,
				randomize: false,
				componentSpacing: 100,
				nodeRepulsion: 400000,
				edgeElasticity: 100,
				nestingFactor: 5,
				gravity: 80,
				numIter: 1000,
				initialTemp: 200,
				coolingFactor: 0.95,
				minTemp: 1.0
			}
		});

		// Center on the main node
		const centerNodeObj = cy.getElementById(centerNode);
		if (centerNodeObj && centerNodeObj.length > 0) {
			cy.center(centerNodeObj);
		}

		// Add click handler for nodes
		cy.on('tap', 'node', function(evt: any) {
			const node = evt.target;
			console.log('Node clicked:', node.id(), node.data());
			// Could navigate to provision detail page here
		});

		// Return cleanup function
		return () => {
			if (cy) {
				cy.destroy();
			}
		};
	});
</script>

<div class="graph-visualization-container">
	<div bind:this={container} class="graph-container"></div>
	<div class="graph-legend">
		<div class="legend-item">
			<div class="legend-color" style="background-color: #DC2626;"></div>
			<span>Center Node</span>
		</div>
		<div class="legend-item">
			<div class="legend-color" style="background-color: #4F46E5;"></div>
			<span>Related Node</span>
		</div>
		<div class="legend-item">
			<div class="legend-line" style="background-color: #6366F1;"></div>
			<span>Parent/Child</span>
		</div>
		<div class="legend-item">
			<div class="legend-line legend-dashed" style="background-color: #8B5CF6;"></div>
			<span>References</span>
		</div>
	</div>
</div>

<style>
	.graph-visualization-container {
		position: relative;
		width: 100%;
	}

	.graph-container {
		width: 100%;
		height: 600px;
		border: 1px solid var(--color-neutral-200);
		border-radius: 0.5rem;
		background-color: var(--color-neutral-50);
	}

	:global(.dark) .graph-container {
		border-color: var(--color-neutral-700);
		background-color: var(--color-neutral-900);
	}

	.graph-legend {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background-color: white;
		border: 1px solid var(--color-neutral-200);
		border-radius: 0.5rem;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.75rem;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
	}

	:global(.dark) .graph-legend {
		background-color: var(--color-neutral-800);
		border-color: var(--color-neutral-700);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.legend-color {
		width: 1rem;
		height: 1rem;
		border-radius: 50%;
	}

	.legend-line {
		width: 1.5rem;
		height: 2px;
	}

	.legend-dashed {
		background-image: linear-gradient(to right, currentColor 50%, transparent 50%);
		background-size: 8px 2px;
		background-repeat: repeat-x;
	}

	.legend-item span {
		color: var(--color-neutral-700);
	}

	:global(.dark) .legend-item span {
		color: var(--color-neutral-300);
	}
</style>
