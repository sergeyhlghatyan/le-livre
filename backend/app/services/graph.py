"""
Graph traversal and analysis services for provision relationships.

This module provides graph-based analysis capabilities including:
- Impact radius: Multi-hop traversal showing how changes propagate through relationships
- Change constellation: Pattern detection for multi-provision changes over time
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import get_neo4j_driver


def calculate_change_magnitude(text_delta: int) -> float:
    """
    Normalize text_delta to 0-1 scale for visual encoding.

    Args:
        text_delta: Absolute character difference between versions

    Returns:
        Normalized magnitude score (0.0-1.0)

    Scale:
        0-100 chars: 0.0-0.3 (minor tweaks)
        100-500 chars: 0.3-0.7 (moderate changes)
        500+ chars: 0.7-1.0 (major changes)
    """
    if text_delta == 0:
        return 0.0
    if text_delta < 100:
        return 0.3 * (text_delta / 100)
    if text_delta < 500:
        return 0.3 + 0.4 * ((text_delta - 100) / 400)
    return min(1.0, 0.7 + 0.3 * ((text_delta - 500) / 1000))


def get_impact_radius(
    provision_id: str,
    year: int,
    depth: int = 2,
    include_hierarchical: bool = True,
    include_references: bool = True,
    include_amendments: bool = False
) -> Dict[str, Any]:
    """
    Traverse Neo4j relationships to build impact radius graph.

    Algorithm:
    1. Start from central provision at specified year
    2. Breadth-first traversal up to depth levels
    3. Track distance (hop count) for each discovered node
    4. Include specified relationship types
    5. For each node, fetch change data via AMENDED_FROM relationships
    6. Return nodes with distance metadata, edges, and statistics

    Args:
        provision_id: Starting provision ID (e.g., "18/922/a/1")
        year: Year to analyze
        depth: Maximum traversal depth (1-3 hops)
        include_hierarchical: Include PARENT_OF relationships
        include_references: Include REFERENCES relationships
        include_amendments: Include AMENDED_FROM relationships

    Returns:
        Dictionary with keys:
            - central_provision: provision_id
            - year: analysis year
            - depth: max depth used
            - nodes: List of dicts with id, label, heading, distance, change_type, magnitude, text_delta
            - edges: List of dicts with source, target, type
            - stats: Dict with counts by change_type
    """
    driver = get_neo4j_driver()

    # Build relationship type filter for Cypher query
    rel_types = []
    if include_hierarchical:
        rel_types.extend(['PARENT_OF', 'CHILD_OF'])
    if include_references:
        rel_types.extend(['REFERENCES', 'REFERENCED_BY'])
    if include_amendments:
        rel_types.append('AMENDED_FROM')

    if not rel_types:
        # No relationships to traverse
        return {
            'central_provision': provision_id,
            'year': year,
            'depth': depth,
            'nodes': [],
            'edges': [],
            'stats': {'total': 0}
        }

    # Cypher query for breadth-first traversal with distance tracking
    query = f"""
    MATCH (central:Provision {{provision_id: $provision_id, year: $year}})
    CALL apoc.path.subgraphAll(central, {{
        relationshipFilter: '{"|".join(rel_types)}',
        minLevel: 0,
        maxLevel: $depth
    }})
    YIELD nodes, relationships

    // Calculate distance for each node
    UNWIND nodes AS node
    OPTIONAL MATCH path = shortestPath((central)-[*0..{depth}]->(node))
    WITH node, length(path) as distance

    // Fetch change data via AMENDED_FROM
    OPTIONAL MATCH (node)-[amendment:AMENDED_FROM]->(previous:Provision)
    WHERE previous.year = node.year - 1 OR previous.year < node.year
    WITH node, distance,
         COALESCE(amendment.change_type, 'unchanged') as change_type,
         COALESCE(amendment.text_delta, 0) as text_delta
    ORDER BY previous.year DESC
    LIMIT 1

    RETURN
        node.provision_id as provision_id,
        node.heading as heading,
        node.year as year,
        distance,
        change_type,
        text_delta
    ORDER BY distance, provision_id
    """

    # Query for edges
    edges_query = f"""
    MATCH (central:Provision {{provision_id: $provision_id, year: $year}})
    CALL apoc.path.subgraphAll(central, {{
        relationshipFilter: '{"|".join(rel_types)}',
        minLevel: 0,
        maxLevel: $depth
    }})
    YIELD relationships

    UNWIND relationships AS rel
    RETURN
        startNode(rel).provision_id as source,
        endNode(rel).provision_id as target,
        type(rel) as rel_type
    """

    nodes = []
    edges = []
    stats = {
        'total': 0,
        'added': 0,
        'modified': 0,
        'removed': 0,
        'unchanged': 0
    }

    with driver.session() as session:
        # Fetch nodes with change data
        result = session.run(query, provision_id=provision_id, year=year, depth=depth)

        for record in result:
            text_delta = record['text_delta']
            magnitude = calculate_change_magnitude(text_delta)
            change_type = record['change_type']

            node = {
                'id': record['provision_id'],
                'label': record['provision_id'],
                'heading': record['heading'],
                'distance': record['distance'] or 0,
                'change_type': change_type,
                'magnitude': magnitude,
                'text_delta': text_delta
            }
            nodes.append(node)

            stats['total'] += 1
            stats[change_type] = stats.get(change_type, 0) + 1

        # Fetch edges
        edge_result = session.run(edges_query, provision_id=provision_id, year=year, depth=depth)

        for record in edge_result:
            edges.append({
                'source': record['source'],
                'target': record['target'],
                'type': record['rel_type']
            })

    return {
        'central_provision': provision_id,
        'year': year,
        'depth': depth,
        'nodes': nodes,
        'edges': edges,
        'stats': stats
    }


def get_change_constellation(
    provision_id: Optional[str] = None,
    section_num: Optional[str] = None,
    year_start: int = 2010,
    year_end: int = 2024,
    change_types: Optional[List[str]] = None,
    min_magnitude: float = 0.0
) -> Dict[str, Any]:
    """
    Find multi-provision change patterns in specified year range.

    Algorithm:
    1. Query provisions with AMENDED_FROM relationships in year range
    2. Filter by change_type and magnitude threshold
    3. Group provisions by (year, parent_provision_id) for clustering
    4. Build edges between related provisions (PARENT_OF, REFERENCES)
    5. Return nodes, edges, and cluster metadata

    Args:
        provision_id: Optional filter for specific provision or its descendants
        section_num: Optional filter for specific section (e.g., "18/922")
        year_start: Start of year range (inclusive)
        year_end: End of year range (inclusive)
        change_types: Optional list of change types to include (['added', 'modified', 'removed'])
        min_magnitude: Minimum change magnitude threshold (0.0-1.0)

    Returns:
        Dictionary with keys:
            - year_range: Tuple of (year_start, year_end)
            - nodes: List of ConstellationNode dicts
            - edges: List of edge dicts
            - clusters: List of cluster metadata dicts
    """
    driver = get_neo4j_driver()

    # Build filters
    filters = ["amendment.change_type IS NOT NULL"]

    if provision_id:
        filters.append("(p.provision_id = $provision_id OR p.provision_id STARTS WITH $provision_id + '/')")

    if section_num:
        filters.append("p.section_num = $section_num")

    if change_types:
        filters.append("amendment.change_type IN $change_types")

    filter_clause = " AND ".join(filters)

    # Query for changed provisions with clustering
    query = f"""
    MATCH (p:Provision)-[amendment:AMENDED_FROM]->(prev:Provision)
    WHERE p.year >= $year_start AND p.year <= $year_end
      AND {filter_clause}

    // Get parent for clustering
    OPTIONAL MATCH (parent:Provision)-[:PARENT_OF]->(p)
    WHERE parent.year = p.year

    WITH p, amendment, parent,
         COALESCE(amendment.text_delta, 0) as text_delta

    // Calculate magnitude
    WITH p, amendment, parent, text_delta,
         CASE
           WHEN text_delta = 0 THEN 0.0
           WHEN text_delta < 100 THEN 0.3 * (text_delta * 1.0 / 100)
           WHEN text_delta < 500 THEN 0.3 + 0.4 * ((text_delta - 100) * 1.0 / 400)
           ELSE 1.0
         END as magnitude

    WHERE magnitude >= $min_magnitude

    RETURN
        p.provision_id as provision_id,
        p.heading as heading,
        p.year as year,
        amendment.change_type as change_type,
        magnitude,
        text_delta,
        COALESCE(parent.provision_id, 'root') as parent_id
    ORDER BY p.year, parent_id, p.provision_id
    """

    # Query for edges between changed provisions
    edges_query = f"""
    MATCH (p:Provision)-[amendment:AMENDED_FROM]->()
    WHERE p.year >= $year_start AND p.year <= $year_end
      AND {filter_clause}

    WITH collect(DISTINCT p.provision_id) as changed_ids

    MATCH (p1:Provision)-[rel:PARENT_OF|REFERENCES]-(p2:Provision)
    WHERE p1.provision_id IN changed_ids
      AND p2.provision_id IN changed_ids
      AND p1.year = p2.year

    RETURN
        p1.provision_id as source,
        p2.provision_id as target,
        type(rel) as rel_type
    """

    nodes = []
    edges = []
    clusters_dict: Dict[Tuple[int, str], List[str]] = {}

    params = {
        'year_start': year_start,
        'year_end': year_end,
        'min_magnitude': min_magnitude
    }

    if provision_id:
        params['provision_id'] = provision_id
    if section_num:
        params['section_num'] = section_num
    if change_types:
        params['change_types'] = change_types

    with driver.session() as session:
        # Fetch nodes
        result = session.run(query, **params)

        for record in result:
            node = {
                'id': record['provision_id'],
                'label': record['provision_id'],
                'heading': record['heading'],
                'year': record['year'],
                'change_type': record['change_type'],
                'magnitude': record['magnitude'],
                'cluster_id': None  # Will be assigned below
            }
            nodes.append(node)

            # Group for clustering
            cluster_key = (record['year'], record['parent_id'])
            if cluster_key not in clusters_dict:
                clusters_dict[cluster_key] = []
            clusters_dict[cluster_key].append(record['provision_id'])

        # Assign cluster IDs
        clusters = []
        for idx, ((year, parent_id), provision_ids) in enumerate(clusters_dict.items()):
            cluster_id = idx
            clusters.append({
                'cluster_id': cluster_id,
                'year': year,
                'parent_id': parent_id,
                'provisions': provision_ids,
                'count': len(provision_ids)
            })

            # Update nodes with cluster_id
            for node in nodes:
                if node['id'] in provision_ids and node['year'] == year:
                    node['cluster_id'] = cluster_id

        # Fetch edges
        edge_result = session.run(edges_query, **params)

        for record in edge_result:
            edges.append({
                'source': record['source'],
                'target': record['target'],
                'type': record['rel_type']
            })

    return {
        'year_range': (year_start, year_end),
        'nodes': nodes,
        'edges': edges,
        'clusters': clusters
    }
