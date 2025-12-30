<script lang="ts">
	import { api, type GraphResponse, type GraphNode } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Legend from '$lib/components/graph/Legend.svelte';
	import InfoPanel from '$lib/components/graph/InfoPanel.svelte';
	import GraphStats from '$lib/components/graph/GraphStats.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import Breadcrumb, { type BreadcrumbItem } from '$lib/components/ui/Breadcrumb.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { onMount } from 'svelte';

	// Browser-only imports - will be dynamically imported
	let Graph: any;
	let Sigma: any;
	let circular: any;
	let forceAtlas2: any;

	// State declarations
	let sectionNum = $state('922');
	let year = $state(2024);
	let loading = $state(false);
	let loadingSections = $state(true);
	let loadingYears = $state(false);
	let error = $state('');
	let graphData = $state<GraphResponse | null>(null);
	let selectedNode = $state<GraphNode | null>(null);
	let layout = $state<'hierarchical' | 'force'>('hierarchical');
	let searchQuery = $state('');
	let showParentOf = $state(true);
	let showReferences = $state(true);

	let sections = $state<Array<{ section_num: string; heading: string }>>([]);
	let availableYears = $state<number[]>([]);

	let sigmaContainer = $state<HTMLDivElement>();
	let sigma: Sigma | null = null;
	let graph: Graph | null = null;

	// Expansion state
	let expandedNodes = $state<Set<string>>(new Set());
	let loadingChildren = $state<Set<string>>(new Set());
	let nodeMetadata = $state<Map<string, {
		hasChildren: boolean;
		childrenLoaded: boolean;
		childCount: number;
	}>>(new Map());

	const provisionId = $derived(`/us/usc/t18/s${sectionNum}`);

	// Auth guard and dynamic imports
	onMount(async () => {
		if (!auth.isAuthenticated && !auth.loading) {
			goto('/login');
			return;
		}

		// Dynamically import browser-only libraries
		if (browser) {
			const graphologyModule = await import('graphology');
			const sigmaModule = await import('sigma');
			const circularModule = await import('graphology-layout');
			const forceAtlas2Module = await import('graphology-layout-forceatlas2');

			Graph = graphologyModule.default;
			Sigma = sigmaModule.default;
			circular = circularModule.circular;
			forceAtlas2 = forceAtlas2Module.default;

			// Load available sections
			try {
				sections = await api.getSections();
				loadingSections = false;

				// Check for query parameters
				const sectionParam = $page.url.searchParams.get('section');
				const yearParam = $page.url.searchParams.get('year');

				if (sectionParam) {
					sectionNum = sectionParam;
				}

				// Load available years for the section
				await loadYears();

				if (yearParam) {
					const parsedYear = parseInt(yearParam);
					if (availableYears.includes(parsedYear)) {
						year = parsedYear;
					}
				}

				// Auto-load graph
				loadGraph();
			} catch (err) {
				error = err instanceof Error ? err.message : 'Failed to load sections';
				loadingSections = false;
			}
		}
	});

	async function loadYears() {
		loadingYears = true;
		try {
			availableYears = await api.getSectionYears(sectionNum);
			// Set year to latest available if current year not in list
			if (availableYears.length > 0 && !availableYears.includes(year)) {
				year = availableYears[0];
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load years';
		} finally {
			loadingYears = false;
		}
	}

	// Watch for section changes
	$effect(() => {
		if (browser && sectionNum && !loadingSections) {
			loadYears();
		}
	});

	// Level colors for nodes
	const levelColors: Record<string, string> = {
		section: '#3B82F6',
		subsection: '#10B981',
		paragraph: '#F59E0B',
		subparagraph: '#8B5CF6',
		clause: '#EC4899'
	};

	const breadcrumbItems = $derived<BreadcrumbItem[]>([
		{ label: 'Home', href: '/' },
		{ label: 'Graph', href: undefined },
		...(graphData ? [{ label: provisionId }] : [])
	]);

	// Initialize Sigma when container and data are ready
	$effect(() => {
		if (graphData && sigmaContainer) {
			if (sigma) {
				sigma.kill();
			}
			if (graph) {
				graph.clear();
			}
			initializeSigma(graphData);
		}
	});

	// Update graph when filters change
	$effect(() => {
		if (sigma && graph) {
			updateEdgeVisibility();
		}
	});

	// Search functionality
	$effect(() => {
		if (sigma && graph && searchQuery) {
			highlightSearchResults();
		} else if (sigma && graph) {
			// Reset highlighting
			graph.forEachNode((node) => {
				graph.setNodeAttribute(node, 'highlighted', false);
			});
			sigma.refresh();
		}
	});

	// Cleanup on unmount
	$effect(() => {
		return () => {
			if (sigma) {
				sigma.kill();
				sigma = null;
			}
			if (graph) {
				graph.clear();
				graph = null;
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
			graphData = data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load graph';
		} finally {
			loading = false;
		}
	}

	async function expandNode(nodeId: string) {
		if (loadingChildren.has(nodeId)) return; // Already loading

		const metadata = nodeMetadata.get(nodeId);
		if (!metadata?.hasChildren) return; // No children to expand
		if (metadata.childrenLoaded) return; // Already loaded

		// Set loading state
		loadingChildren = new Set([...loadingChildren, nodeId]);

		try {
			const response = await api.getGraphChildren(nodeId, year, showReferences);

			// Merge new nodes into graph
			response.nodes.forEach((node) => {
				if (!graph!.hasNode(node.id)) {
					const color = levelColors[node.level] || '#6B7280';
					const size = node.level === 'section' ? 12 : node.level === 'subsection' ? 10 : 8;

					graph!.addNode(node.id, {
						label: node.label,
						level: node.level,
						heading: node.heading,
						x: Math.random(), // Will be repositioned
						y: Math.random(),
						size,
						color,
						originalColor: color,
						highlighted: false
					});

					// Track child metadata
					if (node.child_count && node.child_count > 0) {
						nodeMetadata.set(node.id, {
							hasChildren: true,
							childrenLoaded: false,
							childCount: node.child_count
						});
					}
				}
			});

			// Merge new edges
			response.edges.forEach((edge, idx) => {
				const edgeId = `${edge.source}-${edge.target}-expand-${idx}`;
				if (!graph!.hasEdge(edgeId)) {
					const isReference = edge.type === 'references';
					graph!.addEdge(edge.source, edge.target, {
						id: edgeId,
						edgeType: edge.type,
						label: isReference ? 'refs' : 'parent',
						size: isReference ? 1 : 2,
						color: isReference ? '#9CA3AF' : '#6B7280'
					});
				}
			});

			// Mark as expanded
			expandedNodes = new Set([...expandedNodes, nodeId]);
			metadata.childrenLoaded = true;

			// Re-layout children
			relayoutSubgraph(nodeId);

			sigma?.refresh();

		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to expand node';
		} finally {
			loadingChildren = new Set([...loadingChildren].filter(id => id !== nodeId));
		}
	}

	function collapseNode(nodeId: string) {
		const metadata = nodeMetadata.get(nodeId);
		if (!metadata?.childrenLoaded) return;

		// Find all descendants
		const descendants = getDescendants(nodeId);

		// Remove descendants from graph
		descendants.forEach(descendantId => {
			if (graph!.hasNode(descendantId)) {
				graph!.dropNode(descendantId); // Also removes connected edges
			}

			// Clean up metadata
			expandedNodes.delete(descendantId);
			nodeMetadata.delete(descendantId);
		});

		// Mark as collapsed
		expandedNodes.delete(nodeId);
		metadata.childrenLoaded = false;

		sigma?.refresh();
	}

	function getDescendants(nodeId: string, visited = new Set<string>()): string[] {
		if (visited.has(nodeId)) return [];
		visited.add(nodeId);

		const descendants: string[] = [];

		// Find children via PARENT_OF edges
		graph!.forEachEdge((edge, attrs, source, target) => {
			if (attrs.edgeType === 'parent_of' && source === nodeId) {
				descendants.push(target);
				descendants.push(...getDescendants(target, visited));
			}
		});

		return descendants;
	}

	function relayoutSubgraph(parentNodeId: string) {
		if (!graph || !sigma) return;

		// Get parent position
		const parentAttrs = graph.getNodeAttributes(parentNodeId);
		if (!parentAttrs) return;

		const children: string[] = [];
		graph.forEachEdge((edge, attrs, source, target) => {
			if (attrs.edgeType === 'parent_of' && source === parentNodeId) {
				children.push(target);
			}
		});

		if (children.length === 0) return;

		// Position children in a circle around parent
		const radius = 0.3; // Relative to viewport
		const angleStep = (2 * Math.PI) / children.length;

		children.forEach((childId, idx) => {
			const angle = idx * angleStep;
			const x = parentAttrs.x + radius * Math.cos(angle);
			const y = parentAttrs.y + radius * Math.sin(angle);

			graph!.setNodeAttribute(childId, 'x', x);
			graph!.setNodeAttribute(childId, 'y', y);
		});
	}

	function initializeSigma(data: GraphResponse) {
		if (!sigmaContainer) {
			console.error('Sigma container not available');
			return;
		}

		if (!Graph || !Sigma || !circular || !forceAtlas2) {
			console.error('Graph libraries not loaded yet');
			return;
		}

		console.log('Initializing Sigma with', data.nodes.length, 'nodes');

		// Create Graphology graph
		graph = new Graph();

			// Add nodes with colors and sizes
		data.nodes.forEach((node) => {
			const color = levelColors[node.level] || '#6B7280';
			const size = node.level === 'section' ? 12 : node.level === 'subsection' ? 10 : 8;

			graph!.addNode(node.id, {
				label: node.label,
				level: node.level,
				heading: node.heading,
				x: Math.random(),
				y: Math.random(),
				size,
				color,
				originalColor: color,
				highlighted: false
			});

			// Initialize metadata for nodes with children
			if (node.child_count && node.child_count > 0) {
				nodeMetadata.set(node.id, {
					hasChildren: true,
					childrenLoaded: false,
					childCount: node.child_count
				});
			}
		});

		// Add edges with labels and styles
		data.edges.forEach((edge, idx) => {
			const edgeId = `${edge.source}-${edge.target}-${idx}`;
			const isReference = edge.type === 'references';

			graph!.addEdge(edge.source, edge.target, {
				id: edgeId,
				edgeType: edge.type, // Store type separately, not as 'type'
				label: isReference ? 'refs' : 'parent',
				size: isReference ? 1 : 2,
				color: isReference ? '#9CA3AF' : '#6B7280'
			});
		});

		// Apply layout
		if (layout === 'hierarchical') {
			circular.assign(graph);
		} else {
			// Force-directed layout
			const settings = forceAtlas2.inferSettings(graph);
			forceAtlas2.assign(graph, { settings, iterations: 50 });
		}

		// Initialize Sigma renderer
		sigma = new Sigma(graph, sigmaContainer, {
			renderEdgeLabels: true,
			defaultNodeColor: '#6B7280',
			defaultEdgeColor: '#D4D4D4',
			labelSize: 10,
			labelFont: 'JetBrains Mono, monospace',
			labelColor: { color: '#171717' },
			edgeLabelSize: 8,
			edgeLabelFont: 'JetBrains Mono, monospace',
			edgeLabelColor: { color: '#737373' }
		});

		// Node click - select and show in info panel
		sigma.on('clickNode', ({ node }) => {
			const nodeData = graphData?.nodes.find((n) => n.id === node);
			if (nodeData) {
				selectedNode = nodeData;
				highlightNeighborhood(node);
			}
		});

		// Double-click - navigate to provision
		sigma.on('doubleClickNode', ({ node }) => {
			navigateToProvision(node);
		});

		// Canvas click - deselect
		sigma.on('clickStage', () => {
			selectedNode = null;
			resetHighlighting();
		});

		// Hover effects
		sigma.on('enterNode', ({ node }) => {
			graph!.setNodeAttribute(node, 'highlighted', true);
			// Dim other nodes
			graph!.forEachNode((n) => {
				if (n !== node) {
					const color = graph!.getNodeAttribute(n, 'originalColor');
					graph!.setNodeAttribute(n, 'color', color + '80'); // Add transparency
				}
			});
			sigma!.refresh();
		});

		sigma.on('leaveNode', ({ node }) => {
			if (!selectedNode) {
				resetHighlighting();
			}
		});

		updateEdgeVisibility();
	}

	function highlightNeighborhood(nodeId: string) {
		if (!graph) return;

		// Reset all
		resetHighlighting();

		// Highlight selected node
		graph.setNodeAttribute(nodeId, 'highlighted', true);

		// Highlight connected edges and neighbor nodes
		const neighbors = new Set(graph.neighbors(nodeId));
		graph.forEachEdge(nodeId, (edge, attributes, source, target) => {
			graph!.setEdgeAttribute(edge, 'color', '#3B82F6');
			graph!.setEdgeAttribute(edge, 'size', attributes.size * 1.5);
		});

		// Dim non-neighbor nodes
		graph.forEachNode((node) => {
			if (node !== nodeId && !neighbors.has(node)) {
				const color = graph!.getNodeAttribute(node, 'originalColor');
				graph!.setNodeAttribute(node, 'color', color + '40'); // More transparent
			}
		});

		sigma?.refresh();
	}

	function resetHighlighting() {
		if (!graph || !sigma) return;

		graph.forEachNode((node) => {
			const originalColor = graph!.getNodeAttribute(node, 'originalColor');
			graph!.setNodeAttribute(node, 'color', originalColor);
			graph!.setNodeAttribute(node, 'highlighted', false);
		});

		graph.forEachEdge((edge) => {
			const isReference = graph!.getEdgeAttribute(edge, 'edgeType') === 'references';
			graph!.setEdgeAttribute(edge, 'color', isReference ? '#9CA3AF' : '#6B7280');
			graph!.setEdgeAttribute(edge, 'size', isReference ? 1 : 2);
		});

		sigma.refresh();
	}

	function highlightSearchResults() {
		if (!graph || !sigma || !searchQuery) return;

		const query = searchQuery.toLowerCase();
		let found = false;

		graph.forEachNode((node) => {
			const label = graph!.getNodeAttribute(node, 'label').toLowerCase();
			const heading = graph!.getNodeAttribute(node, 'heading')?.toLowerCase() || '';

			if (label.includes(query) || heading.includes(query)) {
				graph!.setNodeAttribute(node, 'highlighted', true);
				graph!.setNodeAttribute(node, 'size', graph!.getNodeAttribute(node, 'size') * 1.5);
				found = true;
			} else {
				const color = graph!.getNodeAttribute(node, 'originalColor');
				graph!.setNodeAttribute(node, 'color', color + '40');
			}
		});

		sigma.refresh();
	}

	function updateEdgeVisibility() {
		if (!graph || !sigma) return;

		graph.forEachEdge((edge) => {
			const edgeType = graph!.getEdgeAttribute(edge, 'edgeType');
			let hidden = false;

			if (edgeType === 'references' && !showReferences) {
				hidden = true;
			} else if (edgeType === 'parent_of' && !showParentOf) {
				hidden = true;
			}

			graph!.setEdgeAttribute(edge, 'hidden', hidden);
		});

		sigma.refresh();
	}

	function changeLayout(newLayout: typeof layout) {
		layout = newLayout;
		if (graph && sigma) {
			if (newLayout === 'hierarchical') {
				circular.assign(graph);
			} else {
				const settings = forceAtlas2.inferSettings(graph);
				forceAtlas2.assign(graph, { settings, iterations: 50 });
			}
			sigma.refresh();
		}
	}

	function resetZoom() {
		if (sigma) {
			sigma.getCamera().reset();
		}
	}

	function exportPNG() {
		if (!sigmaContainer) return;

		// Use html2canvas or similar library for export
		// For now, just alert
		alert('Export PNG: Use browser screenshot (Cmd+Shift+4 on Mac, Win+Shift+S on Windows)');
	}

	function navigateToProvision(nodeId: string) {
		goto(`/provision/${encodeURIComponent(nodeId)}?year=${year}`);
	}

	function closeInfoPanel() {
		selectedNode = null;
		resetHighlighting();
	}
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
					Graph: §{sectionNum}
					{#if sections.find(s => s.section_num === sectionNum)}
						- {sections.find(s => s.section_num === sectionNum)?.heading}
					{/if}
				</h1>
			</div>

			<div class="flex items-center gap-2">
				<!-- Section Selector -->
				<select
					bind:value={sectionNum}
					onchange={() => loadGraph()}
					disabled={loadingSections}
					class="px-3 py-1.5 text-xs border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors"
				>
					{#each sections as section}
						<option value={section.section_num}>
							§{section.section_num} - {section.heading}
						</option>
					{/each}
				</select>

				<!-- Year Selector -->
				<select
					bind:value={year}
					onchange={() => loadGraph()}
					disabled={loadingYears}
					class="px-3 py-1.5 text-xs border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors"
				>
					{#each availableYears as y}
						<option value={y}>{y}</option>
					{/each}
				</select>

				{#if graphData}
					<!-- Search -->
					<Input
						bind:value={searchQuery}
						placeholder="Search provisions..."
						class="w-48 text-xs"
					/>

					<!-- Filters -->
					<div class="flex items-center gap-2 px-3 py-1.5 border border-neutral-300 dark:border-neutral-700 rounded-md">
						<label class="flex items-center gap-1.5 text-xs text-neutral-700 dark:text-neutral-300">
							<input type="checkbox" bind:checked={showParentOf} class="rounded" />
							Parent/Child
						</label>
						<label class="flex items-center gap-1.5 text-xs text-neutral-700 dark:text-neutral-300">
							<input type="checkbox" bind:checked={showReferences} class="rounded" />
							References
						</label>
					</div>

					<!-- Layout -->
					<select
						bind:value={layout}
						onchange={() => changeLayout(layout)}
						class="px-3 py-1.5 text-xs border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 rounded-md focus:border-primary focus:outline-none transition-colors"
					>
						<option value="hierarchical">Circular</option>
						<option value="force">Force-Directed</option>
					</select>

					<!-- Controls -->
					<Button variant="ghost" onclick={resetZoom}>Reset Zoom</Button>
					<Button variant="ghost" onclick={exportPNG}>Export</Button>
				{/if}
			</div>
		</div>
	</div>

	{#if !graphData}
		<!-- Loading State -->
		<div class="flex-1 flex items-center justify-center">
			<p class="text-neutral-500 dark:text-neutral-400">
				{loadingSections ? 'Loading sections...' : loading ? 'Loading graph...' : error || 'Initializing...'}
			</p>
		</div>
	{:else}
		<!-- Graph View -->
		<div class="flex-1 relative overflow-hidden">
			<!-- Sigma Container -->
			<div bind:this={sigmaContainer} class="absolute inset-0 bg-white dark:bg-neutral-950"></div>

			<!-- Overlays -->
			{#if graphData}
				<GraphStats nodeCount={graphData.nodes.length} edgeCount={graphData.edges.length} />
				<Legend />
				<InfoPanel
					node={selectedNode}
					{year}
					{nodeMetadata}
					{expandedNodes}
					{loadingChildren}
					onNavigate={navigateToProvision}
					onExpand={expandNode}
					onCollapse={collapseNode}
					onClose={closeInfoPanel}
				/>
			{/if}
		</div>
	{/if}
</div>
