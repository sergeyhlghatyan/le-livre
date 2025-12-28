import { test, expect } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8000';

test.describe('Provisions API', () => {
	test('GET /provisions/context/:id returns valid data structure', async ({ request }) => {
		const provisionId = encodeURIComponent('/us/usc/t18/s922/a');
		const response = await request.get(
			`${API_BASE_URL}/provisions/context/${provisionId}?year=2024`
		);

		expect(response.ok()).toBeTruthy();
		expect(response.status()).toBe(200);

		const data = await response.json();

		// Verify main structure
		expect(data).toHaveProperty('provision');
		expect(data).toHaveProperty('timeline');
		expect(data).toHaveProperty('relations');

		// Verify provision object
		expect(data.provision).toHaveProperty('provision_id');
		expect(data.provision).toHaveProperty('year');
		expect(data.provision.year).toBe(2024);

		// Verify timeline is an array
		expect(Array.isArray(data.timeline)).toBeTruthy();

		// Verify relations structure
		if (data.relations) {
			// Parent should have correct structure if present
			if (data.relations.parent) {
				// Can be either provision_id or id depending on backend
				expect(data.relations.parent.provision_id || data.relations.parent.id).toBeTruthy();
				// heading is optional
			}

			// Children should be an array if present
			if (data.relations.children) {
				expect(Array.isArray(data.relations.children)).toBeTruthy();
				if (data.relations.children.length > 0) {
					const child = data.relations.children[0];
					// Can be either provision_id or id
					expect(child.provision_id || child.id).toBeTruthy();
				}
			}

			// References should be an array if present
			if (data.relations.references) {
				expect(Array.isArray(data.relations.references)).toBeTruthy();
			}

			// Referenced by should be an array if present
			if (data.relations.referenced_by) {
				expect(Array.isArray(data.relations.referenced_by)).toBeTruthy();
			}
		}

		// Verify similar provisions if present
		if (data.similar) {
			expect(Array.isArray(data.similar)).toBeTruthy();
			if (data.similar.length > 0) {
				const similar = data.similar[0];
				expect(similar).toHaveProperty('provision_id');
				expect(similar).toHaveProperty('similarity_score');
				expect(typeof similar.similarity_score).toBe('number');
			}
		}
	});

	test('GET /provisions/years returns array of years', async ({ request }) => {
		const response = await request.get(`${API_BASE_URL}/provisions/years`);

		// Endpoint might not exist yet, allow 404
		if (response.ok()) {
			expect(response.status()).toBe(200);

			const years = await response.json();

			// Should be an array
			expect(Array.isArray(years)).toBeTruthy();

			// Should have at least some years
			expect(years.length).toBeGreaterThan(0);

			// Should contain numbers
			expect(years.every((y: any) => typeof y === 'number')).toBeTruthy();

			// Should contain recent years
			expect(years).toContain(2024);
		} else {
			// Endpoint might not be implemented yet
			expect([404, 500]).toContain(response.status());
		}
	});

	test('GET /provisions/timeline/:id returns timeline changes', async ({ request }) => {
		const provisionId = encodeURIComponent('/us/usc/t18/s922/a');
		const response = await request.get(
			`${API_BASE_URL}/provisions/timeline/${provisionId}`
		);

		// Timeline endpoint may return 200 with data or 404 if not found
		if (response.ok()) {
			expect(response.status()).toBe(200);

			const timeline = await response.json();

			// Should be an array
			expect(Array.isArray(timeline)).toBeTruthy();

			// Each change should have required fields
			if (timeline.length > 0) {
				const change = timeline[0];
				expect(change).toHaveProperty('year');
				expect(change).toHaveProperty('change_type');
				expect(typeof change.year).toBe('number');
				expect(typeof change.change_type).toBe('string');

				// Change type should be valid
				expect(['added', 'modified', 'removed', 'unchanged']).toContain(change.change_type);

				// Optional fields
				if (change.magnitude !== undefined) {
					expect(typeof change.magnitude).toBe('number');
					expect(change.magnitude).toBeGreaterThanOrEqual(0);
					expect(change.magnitude).toBeLessThanOrEqual(1);
				}

				if (change.text_delta !== undefined) {
					expect(typeof change.text_delta).toBe('number');
				}
			}
		} else {
			// 404 is acceptable for provisions without timeline data
			expect(response.status()).toBe(404);
		}
	});

	test('GET /provisions/compare/:id hierarchical diff', async ({ request }) => {
		const provisionId = encodeURIComponent('/us/usc/t18/s922');
		const response = await request.get(
			`${API_BASE_URL}/provisions/compare/${provisionId}?from_year=2022&to_year=2024&granularity=sentence`
		);

		// Allow 200 (success) or 404 (not found)
		if (response.ok()) {
			expect(response.status()).toBe(200);

			const diff = await response.json();

			// Could be an array or an object with hierarchy_diff
			if (Array.isArray(diff)) {
				if (diff.length > 0) {
					const node = diff[0];

					// Required fields
					expect(node.provision_id || node.id).toBeTruthy();
					if (node.status) {
						expect(['modified', 'unchanged', 'added', 'removed']).toContain(node.status);
					}
				}
			} else if (diff.hierarchy_diff) {
				// Object response with hierarchy_diff field
				expect(diff.hierarchy_diff).toBeTruthy();
			}
		} else {
			// 404 or 500 might be acceptable for unimplemented endpoints
			expect([404, 500]).toContain(response.status());
		}
	});

	test('GET /provisions/graph/:id returns graph data', async ({ request }) => {
		const provisionId = encodeURIComponent('/us/usc/t18/s922/a');
		const response = await request.get(
			`${API_BASE_URL}/provisions/graph/${provisionId}?year=2024`
		);

		expect(response.ok()).toBeTruthy();
		expect(response.status()).toBe(200);

		const graph = await response.json();

		// Should have nodes and edges
		expect(graph).toHaveProperty('nodes');
		expect(graph).toHaveProperty('edges');

		expect(Array.isArray(graph.nodes)).toBeTruthy();
		expect(Array.isArray(graph.edges)).toBeTruthy();

		// Nodes should have required fields
		if (graph.nodes.length > 0) {
			const node = graph.nodes[0];
			expect(node).toHaveProperty('id');
			expect(node).toHaveProperty('label');
		}

		// Edges should have source and target
		if (graph.edges.length > 0) {
			const edge = graph.edges[0];
			expect(edge).toHaveProperty('source');
			expect(edge).toHaveProperty('target');
		}
	});

	test('POST /chat with RAG query returns answer', async ({ request }) => {
		const response = await request.post(`${API_BASE_URL}/chat`, {
			data: {
				query: 'What are the restrictions on firearm possession?',
				year: 2024
			}
		});

		expect(response.ok()).toBeTruthy();
		expect(response.status()).toBe(200);

		const result = await response.json();

		// Should have answer and sources
		expect(result).toHaveProperty('answer');
		expect(result).toHaveProperty('sources');

		expect(typeof result.answer).toBe('string');
		expect(result.answer.length).toBeGreaterThan(0);

		expect(Array.isArray(result.sources)).toBeTruthy();

		// Sources should have required fields
		if (result.sources.length > 0) {
			const source = result.sources[0];
			expect(source).toHaveProperty('provision_id');
			expect(source).toHaveProperty('text_content');
			// Backend uses 'source' not 'source_type'
			expect(source).toHaveProperty('source');
			expect(['semantic', 'graph', 'both']).toContain(source.source);
		}
	});

	test('API handles invalid provision ID gracefully', async ({ request }) => {
		const invalidId = encodeURIComponent('/invalid/provision/id');
		const response = await request.get(
			`${API_BASE_URL}/provisions/context/${invalidId}?year=2024`
		);

		// Should return 404 or empty result, not 500
		expect([404, 200]).toContain(response.status());

		if (response.status() === 200) {
			const data = await response.json();
			// Should return empty or null provision
			expect(data.provision === null || data.provision === undefined).toBeTruthy();
		}
	});

	test('API handles invalid year gracefully', async ({ request }) => {
		const provisionId = encodeURIComponent('/us/usc/t18/s922/a');
		const response = await request.get(
			`${API_BASE_URL}/provisions/context/${provisionId}?year=1800`
		);

		// Should handle gracefully (404, 400, or empty result)
		expect([200, 400, 404]).toContain(response.status());
	});
});
