const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Auth interfaces
export interface User {
	id: number;
	email: string;
	is_active: boolean;
	is_superuser: boolean;
}

export interface ChatRequest {
	query: string;
	year?: number;
	limit?: number;
}

export interface ChatResponse {
	query: string;
	answer: string;
	sources: Source[];
	semantic_count: number;
	graph_count: number;
	both_count?: number;  // Provisions found via both semantic and graph
	year_used: number;  // Year used for the search
}

export interface Source {
	provision_id: string;
	section_num: string;
	year: number;
	provision_level: string;
	provision_num: string;
	text_content: string;
	heading?: string;
	similarity?: number;
	relationship?: string;
	source: 'semantic' | 'graph';
	found_via?: string[];  // Array of sources: ['semantic'], ['graph'], or ['semantic', 'graph']
}

export interface Provision {
	provision_id: string;
	section_num: string;
	year: number;
	provision_level: string;
	provision_num: string;
	text_content: string;
	heading?: string;
}

export interface TimelineResponse {
	section_num: string;
	years: number[];
}

export interface CompareRequest {
	provision_id: string;
	year_old: number;
	year_new: number;
}

export interface CompareResponse {
	provision_id: string;
	year_old: number;
	year_new: number;
	old_provision: Provision;
	new_provision: Provision;
	diff: string[];
	has_changes: boolean;
}

export interface InlineDiffPart {
	type: 'unchanged' | 'added' | 'removed';
	text: string;
}

export interface HierarchyNode {
	provision_id: string;
	provision_level: string;
	provision_num: string;
	heading?: string;
	status: 'unchanged' | 'modified' | 'added' | 'removed';
	text_changed?: boolean;
	old_text?: string;
	new_text?: string;
	inline_diff?: {
		sentence?: InlineDiffPart[];  // Sentence-level diff
		word?: InlineDiffPart[];  // Word-level diff (when requested)
	};
	children: HierarchyNode[];
}

export interface CompareHierarchicalRequest {
	provision_id: string;
	year_old: number;
	year_new: number;
	granularity?: 'word' | 'sentence';
}

export interface CompareHierarchicalResponse {
	provision_id: string;
	year_old: number;
	year_new: number;
	hierarchy_diff: HierarchyNode;
}

export interface GraphNode {
	id: string;
	label: string;
	level: string;
	heading?: string;
}

export interface GraphEdge {
	source: string;
	target: string;
	type: 'parent_of' | 'references';
	display_text?: string;
}

export interface GraphResponse {
	nodes: GraphNode[];
	edges: GraphEdge[];
}

export interface ProvisionPreview {
	heading: string;
	text_content: string;
}

export interface TimelineChange {
	year: number;
	change_type: 'added' | 'modified' | 'removed' | 'unchanged';
	magnitude?: number;  // 0-1 scale indicating severity of changes
	text_delta?: number; // Character difference
}

// Provision Context API Types (Phase 3)
export interface RelationsData {
	parent: Provision | null;
	children: Provision[];
	references: Provision[];       // Provisions this one references
	referenced_by: Provision[];    // Provisions that reference this one
}

export interface AmendmentData {
	year: number;
	change_type: 'added' | 'modified' | 'removed';
	magnitude: number;             // 0.0 - 1.0 change significance
	description: string;           // e.g., "Modified text content"
}

export interface DefinitionsData {
	terms_defined: string[];       // Terms defined by this provision
	terms_used: string[];          // Terms used from other provisions
}

export interface SimilarProvisionData {
	provision_id: string;
	heading?: string;
	text_content: string;
	similarity_score: number;      // 0.0 - 1.0 cosine similarity
}

export interface ProvisionContext {
	provision: Provision;
	timeline: number[];            // Years provision existed
	relations: RelationsData;
	amendments: AmendmentData[];
	definitions: DefinitionsData;
	similar: SimilarProvisionData[];
}

// Phase 4: Impact Radius & Change Constellation
export interface ImpactNode {
	id: string;
	label: string;
	heading?: string;
	distance: number;
	change_type: string; // 'added', 'modified', 'removed', 'unchanged'
	magnitude: number; // 0-1
	text_delta: number;
}

export interface ImpactRadiusResponse {
	central_provision: string;
	year: number;
	depth: number;
	nodes: ImpactNode[];
	edges: GraphEdge[];
	stats: Record<string, number>;
}

export interface ConstellationNode {
	id: string;
	label: string;
	heading?: string;
	year: number;
	change_type: string;
	magnitude: number;
	cluster_id?: number;
}

export interface ChangeConstellationResponse {
	year_range: [number, number];
	nodes: ConstellationNode[];
	edges: GraphEdge[];
	clusters: Array<{
		cluster_id: number;
		year: number;
		parent_id: string;
		provisions: string[];
		count: number;
	}>;
}

export const api = {
	// Auth endpoints
	async login(email: string, password: string): Promise<User> {
		const response = await fetch(`${API_BASE_URL}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({ email, password })
		});

		if (!response.ok) {
			throw new Error('Login failed');
		}

		return response.json();
	},

	async logout(): Promise<void> {
		await fetch(`${API_BASE_URL}/auth/logout`, {
			method: 'POST',
			credentials: 'include'
		});
	},

	async getMe(): Promise<User> {
		const response = await fetch(`${API_BASE_URL}/auth/me`, {
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error('Not authenticated');
		}

		return response.json();
	},

	async refreshToken(): Promise<void> {
		const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
			method: 'POST',
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error('Refresh failed');
		}
	},

	async chat(request: ChatRequest): Promise<ChatResponse> {
		const response = await fetch(`${API_BASE_URL}/chat`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`Chat failed: ${response.statusText}`);
		}

		return response.json();
	},

	async getTimeline(section: string): Promise<TimelineResponse> {
		const response = await fetch(`${API_BASE_URL}/provisions/timeline/${section}`, {
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error(`Failed to get timeline: ${response.statusText}`);
		}

		return response.json();
	},

	async getProvisions(section: string, year: number): Promise<Provision[]> {
		const response = await fetch(`${API_BASE_URL}/provisions/${section}/${year}`, {
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error(`Failed to get provisions: ${response.statusText}`);
		}

		return response.json();
	},

	async compareProvisions(request: CompareRequest): Promise<CompareResponse> {
		const response = await fetch(`${API_BASE_URL}/provisions/compare`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`Comparison failed: ${response.statusText}`);
		}

		return response.json();
	},

	async compareHierarchical(
		request: CompareHierarchicalRequest,
		timeoutMs: number = 60000  // 60 second default timeout
	): Promise<CompareHierarchicalResponse> {
		console.log('[Compare API] Request started:', request);
		const controller = new AbortController();
		const timeoutId = setTimeout(() => {
			console.log('[Compare API] Timeout triggered after', timeoutMs, 'ms');
			controller.abort();
		}, timeoutMs);

		try {
			console.log('[Compare API] Sending fetch request...');
			const response = await fetch(`${API_BASE_URL}/provisions/compare/hierarchical`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify(request),
				signal: controller.signal
			});

			console.log('[Compare API] Response received:', {
				status: response.status,
				statusText: response.statusText,
				contentLength: response.headers.get('content-length'),
				contentType: response.headers.get('content-type')
			});

			clearTimeout(timeoutId);

			if (!response.ok) {
				console.error('[Compare API] Response not OK:', response.status, response.statusText);
				throw new Error(`Hierarchical comparison failed: ${response.statusText}`);
			}

			console.log('[Compare API] Parsing JSON response...');
			const startParse = Date.now();
			const data = await response.json();
			const parseTime = Date.now() - startParse;
			console.log('[Compare API] JSON parsed successfully in', parseTime, 'ms, data size:', JSON.stringify(data).length, 'chars');

			return data;
		} catch (err) {
			console.error('[Compare API] Error occurred:', err);
			clearTimeout(timeoutId);
			if (err instanceof Error && err.name === 'AbortError') {
				throw new Error('Comparison timed out. The request is taking longer than expected. Please try a smaller provision or check the backend.');
			}
			throw err;
		}
	},

	async getGraph(provisionId: string, year: number = 2024): Promise<GraphResponse> {
		const response = await fetch(
			`${API_BASE_URL}/provisions/graph/${encodeURIComponent(provisionId)}?year=${year}`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			throw new Error(`Failed to get graph: ${response.statusText}`);
		}

		return response.json();
	},

	async getProvision(provisionId: string, year: number): Promise<Provision> {
		const response = await fetch(
			`${API_BASE_URL}/provisions/provision/${encodeURIComponent(provisionId)}/${year}`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			throw new Error(`Failed to get provision: ${response.statusText}`);
		}

		return response.json();
	},

	async getProvisionPreview(provisionId: string, year: number): Promise<ProvisionPreview> {
		const response = await fetch(
			`${API_BASE_URL}/provisions/provision/${encodeURIComponent(provisionId)}/${year}`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			// Throw error with status code for better error handling
			if (response.status === 404) {
				throw new Error(`Provision not found (404): ${provisionId} in year ${year}`);
			}
			throw new Error(`Failed to get provision preview: ${response.statusText}`);
		}

		const data = await response.json();
		return {
			heading: data.heading || 'No heading',
			text_content: data.text_content || 'No content available'
		};
	},

	async getProvisionTimelineChanges(provisionId: string): Promise<TimelineChange[]> {
		const response = await fetch(
			`${API_BASE_URL}/provisions/timeline/${encodeURIComponent(provisionId)}/changes`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			throw new Error(`Failed to get timeline changes: ${response.statusText}`);
		}

		return response.json();
	},

	/**
	 * Get comprehensive provision context (Phase 0 API)
	 *
	 * @param provisionId - Full provision ID (e.g., "/us/usc/t18/s922/a/1")
	 * @param year - Year to fetch context for (default: 2024)
	 * @returns Complete provision context with all related data
	 */
	async getProvisionContext(
		provisionId: string,
		year: number = 2024
	): Promise<ProvisionContext> {
		const response = await fetch(
			`${API_BASE_URL}/provisions/context/${encodeURIComponent(provisionId)}?year=${year}`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			throw new Error(`Failed to fetch provision context: ${response.statusText}`);
		}

		return response.json();
	},

	/**
	 * Get impact radius visualization (Phase 4)
	 *
	 * Performs breadth-first graph traversal showing how changes propagate
	 * through provision relationships.
	 *
	 * @param provisionId - Starting provision ID (e.g., "18/922/a/1")
	 * @param year - Year to analyze
	 * @param depth - Maximum traversal depth (1-3 hops, default: 2)
	 * @param includeHierarchical - Include PARENT_OF relationships (default: true)
	 * @param includeReferences - Include REFERENCES relationships (default: true)
	 * @param includeAmendments - Include AMENDED_FROM relationships (default: false)
	 * @returns Impact radius with nodes, edges, and statistics
	 */
	async getImpactRadius(
		provisionId: string,
		year: number,
		depth: number = 2,
		includeHierarchical: boolean = true,
		includeReferences: boolean = true,
		includeAmendments: boolean = false
	): Promise<ImpactRadiusResponse> {
		const params = new URLSearchParams({
			year: year.toString(),
			depth: depth.toString(),
			include_hierarchical: includeHierarchical.toString(),
			include_references: includeReferences.toString(),
			include_amendments: includeAmendments.toString()
		});

		const response = await fetch(
			`${API_BASE_URL}/provisions/impact-radius/${encodeURIComponent(provisionId)}?${params}`,
			{ credentials: 'include' }
		);

		if (!response.ok) {
			throw new Error(`Failed to get impact radius: ${response.statusText}`);
		}

		return response.json();
	},

	/**
	 * Get change constellation visualization (Phase 4)
	 *
	 * Identifies multi-provision change patterns over a year range,
	 * grouped by parent and year for cluster analysis.
	 *
	 * @param provisionId - Optional filter for specific provision or descendants
	 * @param sectionNum - Optional filter for specific section (e.g., "18/922")
	 * @param yearStart - Start of year range (inclusive, default: 2010)
	 * @param yearEnd - End of year range (inclusive, default: 2024)
	 * @param changeTypes - Optional change types to include
	 * @param minMagnitude - Minimum change magnitude (0.0-1.0, default: 0.0)
	 * @returns Change constellation with nodes, edges, and clusters
	 */
	async getChangeConstellation(
		provisionId: string | null,
		sectionNum: string | null,
		yearStart: number,
		yearEnd: number,
		changeTypes?: string[],
		minMagnitude: number = 0.0
	): Promise<ChangeConstellationResponse> {
		const params = new URLSearchParams({
			year_start: yearStart.toString(),
			year_end: yearEnd.toString(),
			min_magnitude: minMagnitude.toString()
		});

		if (provisionId) params.append('provision_id', provisionId);
		if (sectionNum) params.append('section_num', sectionNum);
		if (changeTypes) {
			changeTypes.forEach((ct) => params.append('change_types', ct));
		}

		const response = await fetch(`${API_BASE_URL}/provisions/change-constellation?${params}`, {
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error(`Failed to get change constellation: ${response.statusText}`);
		}

		return response.json();
	},

	/**
	 * Get revision counts for all provisions in a section
	 *
	 * Returns the count of unique years each provision exists in.
	 * This helps identify provisions that have been modified multiple times.
	 *
	 * @param section - Section number (e.g., '922')
	 * @returns Dictionary mapping provision_id to revision count
	 */
	async getProvisionRevisions(section: string): Promise<Record<string, number>> {
		const response = await fetch(`${API_BASE_URL}/provisions/${section}/revisions`, {
			credentials: 'include'
		});

		if (!response.ok) {
			throw new Error(`Failed to get provision revisions: ${response.statusText}`);
		}

		return response.json();
	},

	/**
	 * Batch fetch reference counts for multiple provisions
	 *
	 * Returns the count of how many other provisions reference each provision.
	 * This is a performance-optimized batch endpoint using a single Neo4j query.
	 *
	 * @param provisionIds - Array of provision IDs
	 * @param year - Year to check references for
	 * @returns Dictionary mapping provision_id to reference count
	 */
	async getReferenceCounts(provisionIds: string[], year: number): Promise<Record<string, number>> {
		const response = await fetch(`${API_BASE_URL}/provisions/reference-counts`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({ provision_ids: provisionIds, year })
		});

		if (!response.ok) {
			throw new Error(`Failed to get reference counts: ${response.statusText}`);
		}

		return response.json();
	}
};
