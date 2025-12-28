"""Provisions API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..database import get_postgres_conn, get_neo4j_driver
from ..services.diff import compare_provisions, compare_hierarchical, get_provision_hierarchy
from ..services.rag import hybrid_search
from ..services.context import get_provision_context

router = APIRouter(prefix="/provisions", tags=["provisions"])


class ProvisionResponse(BaseModel):
    """Provision response model."""
    provision_id: str
    section_num: str
    year: int
    provision_level: str
    provision_num: str
    text_content: str
    heading: Optional[str] = None


class TimelineResponse(BaseModel):
    """Timeline response model."""
    section_num: str
    years: List[int]


class CompareRequest(BaseModel):
    """Compare request model."""
    provision_id: str
    year_old: int
    year_new: int


class CompareHierarchicalRequest(BaseModel):
    """Hierarchical compare request model."""
    provision_id: str
    year_old: int
    year_new: int
    granularity: str = "sentence"  # "word" or "sentence"


class GraphNode(BaseModel):
    """Graph node model."""
    id: str
    label: str
    level: str
    heading: Optional[str] = None


class GraphEdge(BaseModel):
    """Graph edge model."""
    source: str
    target: str
    type: str  # "parent_of" or "references"
    display_text: Optional[str] = None


class GraphResponse(BaseModel):
    """Graph response model."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class AmendmentData(BaseModel):
    """Amendment data model."""
    year_old: int
    year_new: int
    change_type: str


class DefinitionUsage(BaseModel):
    """Definition usage model."""
    definition_id: str
    term: str
    confidence: float


class DefinitionProvision(BaseModel):
    """Definition provision model."""
    term: str
    usage_count: int


class DefinitionsData(BaseModel):
    """Definitions data model."""
    uses: List[DefinitionUsage]
    provides: List[DefinitionProvision]


class SimilarProvisionData(BaseModel):
    """Similar provision data model."""
    provision_id: str
    heading: Optional[str]
    text: str
    similarity_score: float


class RelationsData(BaseModel):
    """Relations data model."""
    parent: Optional[Dict[str, Any]]
    children: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    referenced_by: List[Dict[str, Any]]


class ProvisionContextResponse(BaseModel):
    """Provision context response model."""
    provision: ProvisionResponse
    timeline: Optional[List[int]] = None
    relations: Optional[RelationsData] = None
    amendments: Optional[List[AmendmentData]] = None
    definitions: Optional[DefinitionsData] = None
    similar: Optional[List[SimilarProvisionData]] = None


class ImpactNode(BaseModel):
    """Impact radius node model."""
    id: str
    label: str
    heading: Optional[str] = None
    distance: int
    change_type: str  # 'added', 'modified', 'removed', 'unchanged'
    magnitude: float  # 0-1
    text_delta: int


class ImpactRadiusResponse(BaseModel):
    """Impact radius response model."""
    central_provision: str
    year: int
    depth: int
    nodes: List[ImpactNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]  # { "total": 12, "modified": 5, ... }


class ConstellationNode(BaseModel):
    """Change constellation node model."""
    id: str
    label: str
    heading: Optional[str] = None
    year: int
    change_type: str
    magnitude: float
    cluster_id: Optional[int] = None


class ChangeConstellationResponse(BaseModel):
    """Change constellation response model."""
    year_range: tuple[int, int]
    nodes: List[ConstellationNode]
    edges: List[GraphEdge]
    clusters: List[Dict[str, Any]]


# NOTE: More specific routes must come first!
@router.get("/timeline/{section}", response_model=TimelineResponse)
async def get_timeline(section: str):
    """
    Get available years for a section.

    Args:
        section: Section number (e.g., '922')
    """
    try:
        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT year
                FROM provision_embeddings
                WHERE section_num = %s
                ORDER BY year
                """,
                (section,)
            )

            years = [row[0] for row in cur.fetchall()]

            return TimelineResponse(
                section_num=section,
                years=years
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{section}/revisions")
async def get_provision_revisions(section: str):
    """
    Get revision counts for all provisions in a section.

    Returns the count of unique years each provision exists in.
    This helps identify provisions that have been modified multiple times.

    Args:
        section: Section number (e.g., '922')

    Returns:
        Dictionary mapping provision_id to revision count
        Example: {"/us/usc/t18/s922/a": 7, "/us/usc/t18/s922/b": 5}
    """
    try:
        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT provision_id, COUNT(DISTINCT year) as revision_count
                FROM provision_embeddings
                WHERE section_num = %s
                GROUP BY provision_id
                """,
                (section,)
            )

            # Convert to dictionary
            revisions = {row[0]: row[1] for row in cur.fetchall()}

            return revisions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ReferenceCountRequest(BaseModel):
    """Request model for batch reference count lookup."""
    provision_ids: List[str]
    year: int


@router.post("/reference-counts")
async def get_reference_counts(request: ReferenceCountRequest):
    """
    Batch fetch reference counts for multiple provisions.

    Returns the count of how many other provisions reference each provision.
    This is a performance-optimized batch endpoint using a single Neo4j query.

    Args:
        request: ReferenceCountRequest with provision_ids and year

    Returns:
        Dictionary mapping provision_id to reference count
        Example: {"/us/usc/t18/s922/a": 12, "/us/usc/t18/s922/b": 3}
    """
    try:
        driver = get_neo4j_driver()

        with driver.session() as session:
            # Single Neo4j query for all provisions
            query = """
            UNWIND $provision_ids AS provision_id
            OPTIONAL MATCH (p:Provision {id: provision_id, year: $year})
                          <-[:REFERENCES]-(ref:Provision)
            WHERE ref.year = $year
            RETURN provision_id, COUNT(ref) as ref_count
            """

            result = session.run(
                query,
                provision_ids=request.provision_ids,
                year=request.year
            )

            # Convert to dictionary
            counts = {record['provision_id']: record['ref_count'] for record in result}

            # Fill in zeros for provisions with no references
            for provision_id in request.provision_ids:
                if provision_id not in counts:
                    counts[provision_id] = 0

            return counts

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{section}/{year}", response_model=List[ProvisionResponse])
async def get_provisions_by_year(section: str, year: int):
    """
    Get all provisions for a section and year.

    Args:
        section: Section number (e.g., '922')
        year: Year (e.g., 2024)
    """
    try:
        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT provision_id, section_num, year, provision_level,
                       provision_num, text_content, heading
                FROM provision_embeddings
                WHERE section_num = %s AND year = %s
                ORDER BY provision_num
                """,
                (section, year)
            )

            results = []
            for row in cur.fetchall():
                results.append(ProvisionResponse(
                    provision_id=row[0],
                    section_num=row[1],
                    year=row[2],
                    provision_level=row[3],
                    provision_num=row[4],
                    text_content=row[5],
                    heading=row[6]
                ))

            return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare(request: CompareRequest):
    """
    Compare two versions of a provision.

    Returns diff and LLM-generated summary of changes.
    """
    try:
        result = compare_provisions(
            provision_id=request.provision_id,
            year_old=request.year_old,
            year_new=request.year_new
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/hierarchical")
async def compare_hierarchical_endpoint(request: CompareHierarchicalRequest):
    """
    Compare provisions hierarchically at all levels.

    Returns structured hierarchical diff with inline highlighting,
    recursively showing changes at subsection, paragraph, clause,
    subclause levels.
    """
    import logging
    import time
    logger = logging.getLogger(__name__)

    logger.info(f"[Compare] Request received: {request.provision_id} ({request.year_old} -> {request.year_new})")
    start_time = time.time()

    try:
        logger.info(f"[Compare] Calling compare_hierarchical...")
        result = compare_hierarchical(
            provision_id=request.provision_id,
            year_old=request.year_old,
            year_new=request.year_new,
            granularity=request.granularity
        )

        if "error" in result:
            logger.error(f"[Compare] Error in result: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])

        elapsed = time.time() - start_time
        logger.info(f"[Compare] Success! Completed in {elapsed:.2f}s")
        return result

    except HTTPException:
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Compare] Exception after {elapsed:.2f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hierarchy/{provision_id:path}")
async def get_hierarchy(provision_id: str, year: int = 2024):
    """
    Get hierarchical structure of a provision with all children.

    Args:
        provision_id: Provision ID (e.g., '/us/usc/t18/s922/a')
        year: Year (default: 2024)

    Returns:
        Nested hierarchy with provision and all children
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        hierarchy = get_provision_hierarchy(provision_id, year)

        if not hierarchy:
            raise HTTPException(
                status_code=404,
                detail=f"Provision {provision_id} not found for year {year}"
            )

        return hierarchy

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hierarchy: {str(e)}")


@router.get("/graph/{provision_id:path}", response_model=GraphResponse)
async def get_graph(provision_id: str, year: int = 2024):
    """
    Get graph structure for a provision showing hierarchy and references.

    Args:
        provision_id: Provision ID (e.g., '/us/usc/t18/s922/a')
        year: Year (default: 2024)

    Returns:
        Graph with nodes (provisions) and edges (parent_of, references)
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        driver = get_neo4j_driver()

        with driver.session() as session:
            # Query for the provision and its hierarchy + references
            query = """
            // Get the starting provision
            MATCH (p:Provision {id: $provision_id, year: $year})

            // Get all children recursively (up to 3 levels deep)
            OPTIONAL MATCH path1 = (p)-[:PARENT_OF*1..3]->(child:Provision)
            WHERE child.year = $year

            // Get all references from the provision and its children
            OPTIONAL MATCH (p)-[:REFERENCES]->(ref:Provision)
            OPTIONAL MATCH (child)-[:REFERENCES]->(ref2:Provision)
            WHERE child.year = $year

            // Collect all nodes
            WITH p,
                 collect(DISTINCT child) as children,
                 collect(DISTINCT ref) + collect(DISTINCT ref2) as refs,
                 collect(DISTINCT {source: p.id, target: child.id, type: 'parent_of'}) as parent_edges1,
                 [path IN collect(path1) | relationships(path)] as all_parent_paths

            // Flatten parent edges
            UNWIND (CASE WHEN size(all_parent_paths) > 0 THEN all_parent_paths ELSE [[]] END) as parent_path
            UNWIND (CASE WHEN size(parent_path) > 0 THEN parent_path ELSE [null] END) as rel

            WITH p, children, refs,
                 collect(DISTINCT CASE WHEN rel IS NOT NULL
                         THEN {source: startNode(rel).id, target: endNode(rel).id, type: 'parent_of'}
                         END) as parent_edges

            // Get reference edges
            OPTIONAL MATCH (p)-[r:REFERENCES]->(ref:Provision)
            OPTIONAL MATCH (child:Provision)-[r2:REFERENCES]->(ref2:Provision)
            WHERE child IN children

            WITH p, children, refs, parent_edges,
                 collect(DISTINCT {
                     source: p.id,
                     target: ref.id,
                     type: 'references',
                     display_text: r.display_text
                 }) + collect(DISTINCT {
                     source: child.id,
                     target: ref2.id,
                     type: 'references',
                     display_text: r2.display_text
                 }) as ref_edges

            // Combine all nodes and edges
            RETURN p.id as root_id,
                   [p] + children + refs as all_nodes,
                   [e IN parent_edges WHERE e IS NOT NULL] +
                   [e IN ref_edges WHERE e IS NOT NULL] as all_edges
            """

            result = session.run(query, provision_id=provision_id, year=year)
            record = result.single()

            if not record:
                raise HTTPException(
                    status_code=404,
                    detail=f"Provision {provision_id} not found for year {year}"
                )

            # Build nodes list
            nodes = []
            seen_ids = set()

            for node in record["all_nodes"]:
                if node and node["id"] not in seen_ids:
                    seen_ids.add(node["id"])
                    # Extract label from provision ID (e.g., "/us/usc/t18/s922/a" -> "(a)")
                    label = node["num"] if "num" in node else node["id"].split("/")[-1]
                    nodes.append(GraphNode(
                        id=node["id"],
                        label=label,
                        level=node["level"] if "level" in node else "unknown",
                        heading=node.get("heading")
                    ))

            # Build edges list
            edges = []
            for edge in record["all_edges"]:
                if edge and edge["source"] and edge["target"]:
                    edges.append(GraphEdge(
                        source=edge["source"],
                        target=edge["target"],
                        type=edge["type"],
                        display_text=edge.get("display_text")
                    ))

            return GraphResponse(nodes=nodes, edges=edges)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {str(e)}")


@router.get("/provision/{provision_id:path}/{year}", response_model=ProvisionResponse)
async def get_provision_by_id(provision_id: str, year: int):
    """
    Get a single provision by its full ID and year.

    Args:
        provision_id: Full provision ID (e.g., '/us/usc/t18/s922/a')
        year: Year (e.g., 2024)

    Returns:
        Single provision with full text content
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT provision_id, section_num, year, provision_level,
                       provision_num, text_content, heading
                FROM provision_embeddings
                WHERE provision_id = %s AND year = %s
                """,
                (provision_id, year)
            )

            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Provision {provision_id} not found for year {year}"
                )

            return ProvisionResponse(
                provision_id=row[0],
                section_num=row[1],
                year=row[2],
                provision_level=row[3],
                provision_num=row[4],
                text_content=row[5],
                heading=row[6]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_provisions(q: str, year: Optional[int] = None, limit: int = 10):
    """
    Search provisions using hybrid semantic + graph search.

    Args:
        q: Search query
        year: Optional year filter
        limit: Maximum number of results (default: 10)

    Returns:
        Search results with semantic and graph-based matches
    """
    try:
        if not q or len(q.strip()) == 0:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        results = hybrid_search(query=q, limit=limit, year=year)
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/context/{provision_id:path}", response_model=ProvisionContextResponse)
async def get_provision_context_endpoint(
    provision_id: str,
    year: int = 2024,
    include_timeline: bool = True,
    include_relations: bool = True,
    include_amendments: bool = True,
    include_definitions: bool = True,
    include_similar: bool = True
):
    """
    Get rich context for a provision in one API call.

    This endpoint provides comprehensive context including:
    - Base provision data (always included)
    - Timeline: Available years for this provision
    - Relations: Parent, children, references (bidirectional)
    - Amendments: Change history across years
    - Definitions: Terms used and provided by this provision
    - Similar: Semantically similar provisions

    Args:
        provision_id: Full provision ID (e.g., '/us/usc/t18/s922/d')
        year: Year to fetch context for (default: 2024)
        include_timeline: Include available years (default: True)
        include_relations: Include relationships (default: True)
        include_amendments: Include amendment history (default: True)
        include_definitions: Include definition usages (default: True)
        include_similar: Include similar provisions (default: True)

    Returns:
        ProvisionContextResponse with all requested context

    Example:
        GET /provisions/context/us/usc/t18/s922/d?year=2024
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        context = get_provision_context(
            provision_id=provision_id,
            year=year,
            include_timeline=include_timeline,
            include_relations=include_relations,
            include_amendments=include_amendments,
            include_definitions=include_definitions,
            include_similar=include_similar
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Provision {provision_id} not found for year {year}"
            )

        # Convert to response model
        return ProvisionContextResponse(**context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch context: {str(e)}")


@router.get("/timeline/{provision_id:path}/changes")
async def get_provision_timeline_changes(provision_id: str):
    """
    Get timeline change metadata for a provision using AMENDED_FROM relationships.

    Returns change information for each year transition, including:
    - year: The year of the provision version
    - change_type: Type of change (added, modified, removed, unchanged)
    - magnitude: Severity of changes (0-1 scale)
    - text_delta: Character difference between versions

    Args:
        provision_id: Full provision ID (e.g., '/us/usc/t18/s922/d')

    Returns:
        List of TimelineChange objects
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        driver = get_neo4j_driver()

        with driver.session() as session:
            # Query for all years and amendment relationships
            query = """
                // Get all years for this provision
                MATCH (p:Provision {id: $provision_id})
                WITH p.id as pid, collect(DISTINCT p.year) as all_years
                UNWIND all_years as year

                // For each year, check if there's an AMENDED_FROM relationship
                OPTIONAL MATCH (new:Provision {id: pid, year: year})
                              -[a:AMENDED_FROM]->(old:Provision)

                RETURN year,
                       CASE
                           WHEN a IS NOT NULL THEN a.change_type
                           ELSE 'unchanged'
                       END as change_type,
                       CASE
                           WHEN new.text IS NOT NULL AND old.text IS NOT NULL
                           THEN abs(size(new.text) - size(old.text))
                           ELSE 0
                       END as text_delta
                ORDER BY year
            """

            result = session.run(query, provision_id=provision_id)

            changes = []
            for record in result:
                year = record['year']
                change_type = record['change_type']
                text_delta = record['text_delta']

                # Calculate magnitude (0-1 scale based on text delta)
                # Normalize: 0-100 chars = 0.0-0.3, 100-500 = 0.3-0.7, 500+ = 0.7-1.0
                if text_delta == 0:
                    magnitude = 0.0
                elif text_delta < 100:
                    magnitude = 0.3 * (text_delta / 100)
                elif text_delta < 500:
                    magnitude = 0.3 + 0.4 * ((text_delta - 100) / 400)
                else:
                    magnitude = min(1.0, 0.7 + 0.3 * ((text_delta - 500) / 1000))

                changes.append({
                    'year': year,
                    'change_type': change_type,
                    'magnitude': magnitude,
                    'text_delta': text_delta
                })

            return changes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch timeline changes: {str(e)}")


@router.get("/impact-radius/{provision_id:path}", response_model=ImpactRadiusResponse)
async def get_impact_radius_endpoint(
    provision_id: str,
    year: int,
    depth: int = 2,
    include_hierarchical: bool = True,
    include_references: bool = True,
    include_amendments: bool = False
):
    """
    Get impact radius visualization showing how changes propagate through relationships.

    Performs breadth-first graph traversal from the specified provision,
    following relationships up to the specified depth. For each discovered
    provision, fetches change data via AMENDED_FROM relationships.

    Args:
        provision_id: Starting provision ID (e.g., "18/922/a/1")
        year: Year to analyze
        depth: Maximum traversal depth (1-3 hops, default: 2)
        include_hierarchical: Include PARENT_OF relationships (default: True)
        include_references: Include REFERENCES relationships (default: True)
        include_amendments: Include AMENDED_FROM relationships (default: False)

    Returns:
        ImpactRadiusResponse with nodes, edges, and statistics
    """
    try:
        # FastAPI strips leading "/" from path parameters, so add it back if missing
        if not provision_id.startswith('/'):
            provision_id = '/' + provision_id

        from ..services.graph import get_impact_radius

        result = get_impact_radius(
            provision_id=provision_id,
            year=year,
            depth=depth,
            include_hierarchical=include_hierarchical,
            include_references=include_references,
            include_amendments=include_amendments
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get impact radius: {str(e)}")


@router.get("/change-constellation", response_model=ChangeConstellationResponse)
async def get_change_constellation_endpoint(
    provision_id: Optional[str] = None,
    section_num: Optional[str] = None,
    year_start: int = 2010,
    year_end: int = 2024,
    change_types: Optional[List[str]] = None,
    min_magnitude: float = 0.0
):
    """
    Find multi-provision change patterns (constellation) over a year range.

    Identifies provisions that changed together, groups them by parent and year,
    and builds edges between related provisions to visualize change patterns.

    Args:
        provision_id: Optional filter for specific provision or its descendants
        section_num: Optional filter for specific section (e.g., "18/922")
        year_start: Start of year range (inclusive, default: 2010)
        year_end: End of year range (inclusive, default: 2024)
        change_types: Optional list of change types to include (['added', 'modified', 'removed'])
        min_magnitude: Minimum change magnitude threshold (0.0-1.0, default: 0.0)

    Returns:
        ChangeConstellationResponse with nodes, edges, and cluster metadata
    """
    try:
        from ..services.graph import get_change_constellation

        result = get_change_constellation(
            provision_id=provision_id,
            section_num=section_num,
            year_start=year_start,
            year_end=year_end,
            change_types=change_types,
            min_magnitude=min_magnitude
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get change constellation: {str(e)}")
