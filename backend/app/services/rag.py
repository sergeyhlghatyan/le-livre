"""RAG service for semantic and graph-based search."""
from typing import List, Dict, Any
import time
import openai
from openai import OpenAIError
from ..database import get_postgres_conn, get_neo4j_driver
from ..config import get_settings

settings = get_settings()
openai.api_key = settings.openai_api_key


def retry_with_backoff(func, max_retries=3, initial_delay=1.0):
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds

    Returns:
        Function result

    Raises:
        Exception from the last retry attempt
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except (OpenAIError, Exception) as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise last_exception


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a text query with retry logic."""
    def _generate():
        response = openai.embeddings.create(
    model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    return retry_with_backoff(_generate)


def semantic_search(query: str, limit: int = 5, year: int = None) -> List[Dict[str, Any]]:
    """
    Semantic search using vector similarity.

    Args:
        query: Search query
        limit: Number of results
        year: Optional year filter

    Returns:
        List of matching provisions with similarity scores
    """
    query_embedding = generate_embedding(query)

    with get_postgres_conn() as conn:
        cur = conn.cursor()

        if year:
            sql = """
                SELECT
                    provision_id,
                    section_num,
                    year,
                    provision_level,
                    provision_num,
                    text_content,
                    heading,
                    1 - (embedding <=> %s::vector) as similarity
                FROM provision_embeddings
                WHERE year = %s
                  AND (1 - (embedding <=> %s::vector)) >= 0.35
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cur.execute(sql, (query_embedding, year, query_embedding, query_embedding, limit))
        else:
            sql = """
                SELECT
                    provision_id,
                    section_num,
                    year,
                    provision_level,
                    provision_num,
                    text_content,
                    heading,
                    1 - (embedding <=> %s::vector) as similarity
                FROM provision_embeddings
                WHERE (1 - (embedding <=> %s::vector)) >= 0.35
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cur.execute(sql, (query_embedding, query_embedding, query_embedding, limit))

        results = []
        for row in cur.fetchall():
            results.append({
                "provision_id": row[0],
                "section_num": row[1],
                "year": row[2],
                "provision_level": row[3],
                "provision_num": row[4],
                "text_content": row[5],
                "heading": row[6],
                "similarity": float(row[7]),
                "source": "semantic"
            })

        return results


def graph_search(provision_id: str, year: int, relationship_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Graph-based search using Neo4j relationships.

    Includes bidirectional traversal to find:
    - Outgoing relationships (children, references)
    - Parent provisions
    - Sibling provisions (same parent)
    - Incoming references

    Args:
        provision_id: Starting provision ID
        year: Year to search
        relationship_type: Optional relationship filter (CONTAINS, REFERENCES, PARENT_OF)
        limit: Maximum number of results to return

    Returns:
        List of related provisions
    """
    driver = get_neo4j_driver()

    with driver.session(database=settings.neo4j_database) as session:
        if relationship_type:
            # Specific relationship type filter
            query = """
            MATCH (p:Provision {id: $provision_id, year: $year})
            MATCH (p)-[r]->(related:Provision)
            WHERE type(r) = $rel_type AND related.year = $year
            RETURN related.id as provision_id,
                   related.section_num as section_num,
                   related.year as year,
                   related.level as provision_level,
                   related.num as provision_num,
                   related.text as text_content,
                   related.heading as heading,
                   type(r) as relationship
            LIMIT $limit
            """
            result = session.run(query, provision_id=provision_id, year=year, rel_type=relationship_type, limit=limit)
        else:
            # Bidirectional traversal for comprehensive graph context
            query = """
            MATCH (p:Provision {id: $provision_id, year: $year})

            // Get outgoing relationships (children via PARENT_OF, references)
            OPTIONAL MATCH (p)-[r1]->(out:Provision)
            WHERE out.year = $year

            // Get parent provisions (via PARENT_OF)
            OPTIONAL MATCH (parent_prov:Provision)-[:PARENT_OF]->(p)
            WHERE parent_prov.year = $year

            // Get siblings via provision parent (same PARENT_OF parent)
            OPTIONAL MATCH (parent_prov)-[:PARENT_OF]->(sibling_prov:Provision)
            WHERE sibling_prov.year = $year AND sibling_prov.id <> p.id

            // Get siblings via section parent (same CONTAINS parent)
            OPTIONAL MATCH (section:Section)-[:CONTAINS]->(p)
            WHERE section.year = $year
            OPTIONAL MATCH (section)-[:CONTAINS]->(sibling_section:Provision)
            WHERE sibling_section.year = $year AND sibling_section.id <> p.id

            // Get incoming references
            OPTIONAL MATCH (ref:Provision)-[:REFERENCES]->(p)
            WHERE ref.year = $year

            WITH p,
                 collect(DISTINCT {node: out, rel: type(r1)}) as outgoing,
                 collect(DISTINCT {node: parent_prov, rel: 'PARENT_OF'}) as parents,
                 collect(DISTINCT {node: sibling_prov, rel: 'SIBLING'}) as sibling_p,
                 collect(DISTINCT {node: sibling_section, rel: 'SIBLING'}) as sibling_s,
                 collect(DISTINCT {node: ref, rel: 'REFERENCED_BY'}) as refs

            WITH p, outgoing + parents + sibling_p + sibling_s + refs as all_related
            UNWIND all_related as item
            WITH item
            WHERE item.node IS NOT NULL

            RETURN DISTINCT
                   item.node.id as provision_id,
                   item.node.section_num as section_num,
                   item.node.year as year,
                   item.node.level as provision_level,
                   item.node.num as provision_num,
                   item.node.text as text_content,
                   item.node.heading as heading,
                   item.rel as relationship
            LIMIT $limit
            """
            result = session.run(query, provision_id=provision_id, year=year, limit=limit)

        results = []
        for record in result:
            results.append({
                "provision_id": record["provision_id"],
                "section_num": record["section_num"],
                "year": record["year"],
                "provision_level": record["provision_level"],
                "provision_num": record["provision_num"],
                "text_content": record["text_content"],
                "heading": record["heading"],
                "relationship": record["relationship"],
                "source": "graph"
            })

        return results


def hybrid_search(query: str, limit: int = 5, year: int = None, graph_entry_points: int = 3) -> Dict[str, Any]:
    """
    Hybrid search combining semantic and graph-based results.

    Args:
        query: Search query
        limit: Total number of results
        year: Optional year filter
        graph_entry_points: Number of top semantic results to use as graph entry points (default: 3)

    Returns:
        Combined results from semantic and graph search
    """
    # Get semantic results
    semantic_results = semantic_search(query, limit=limit, year=year)

    # Get graph results from top N semantic matches
    graph_results = []
    if semantic_results:
        # Use top N semantic results as entry points for graph traversal
        num_entry_points = min(graph_entry_points, len(semantic_results))
        # Distribute graph limit across entry points
        graph_limit_per_entry = max(3, limit // num_entry_points)

        seen_graph = set()
        for i in range(num_entry_points):
            entry = semantic_results[i]
            entry_graph_results = graph_search(
                provision_id=entry["provision_id"],
                year=entry["year"],
                limit=graph_limit_per_entry
            )
            # Deduplicate graph results from different entry points
            for result in entry_graph_results:
                key = (result["provision_id"], result["year"])
                if key not in seen_graph:
                    seen_graph.add(key)
                    graph_results.append(result)

    # Deduplicate and combine semantic and graph results
    # Track which provisions appear in both semantic and graph
    provision_map = {}  # key -> {provision data + found_via list}

    # Process semantic results first
    for result in semantic_results:
        key = (result["provision_id"], result["year"])
        if key not in provision_map:
            provision_map[key] = {**result, "found_via": ["semantic"]}

    # Process graph results - add or merge with existing
    for result in graph_results:
        key = (result["provision_id"], result["year"])
        if key in provision_map:
            # Already exists from semantic search - mark as found via both
            if "graph" not in provision_map[key]["found_via"]:
                provision_map[key]["found_via"].append("graph")
            # Preserve graph relationship info if not already present
            if "relationship" in result and "relationship" not in provision_map[key]:
                provision_map[key]["relationship"] = result["relationship"]
        else:
            # New provision from graph only
            provision_map[key] = {**result, "found_via": ["graph"]}

    # Convert to list, preserving semantic result ordering where possible
    combined = []

    # Add provisions in order: semantic results first, then graph-only results
    for result in semantic_results:
        key = (result["provision_id"], result["year"])
        if key in provision_map:
            combined.append(provision_map[key])
            del provision_map[key]  # Remove to avoid duplicates

    # Add remaining graph-only results
    for provision in provision_map.values():
        combined.append(provision)

    # Calculate accurate counts after deduplication
    actual_semantic_count = len([r for r in combined if "semantic" in r.get("found_via", [])])
    actual_graph_count = len([r for r in combined if "graph" in r.get("found_via", [])])
    both_count = len([r for r in combined if len(r.get("found_via", [])) > 1])

    return {
        "query": query,
        "semantic_count": actual_semantic_count,
        "graph_count": actual_graph_count,
        "both_count": both_count,  # New field: provisions found in both
        "total_results": len(combined),
        "results": combined[:limit]
    }


def prepare_context_for_llm(results: List[Dict[str, Any]], max_tokens: int = 4000) -> str:
    """
    Intelligently prepare context from search results.

    Priority:
    1. High similarity provisions (> 0.8) - use full text
    2. Referenced provisions or medium similarity - use first 500 chars + heading
    3. Low similarity - use just heading + first 200 chars

    Args:
        results: Search results from hybrid search
        max_tokens: Maximum tokens to use (approximate by characters)

    Returns:
        Formatted context string for LLM
    """
    context_parts = []

    for result in results:
        similarity = result.get('similarity', 0)
        provision_num = result.get('provision_num', '')
        heading = result.get('heading', '')
        text_content = result.get('text_content', '')

        if similarity > 0.8:
            # High match - include full text
            context = f"[{provision_num}] {heading}\n{text_content}"
        elif similarity > 0.5 or result.get('relationship'):
            # Medium match or graph result - include partial text
            context = f"[{provision_num}] {heading}\n{text_content[:500]}..."
        else:
            # Low match - just heading and snippet
            context = f"[{provision_num}] {heading}\n{text_content[:200]}..."

        context_parts.append(context)

    return "\n\n---\n\n".join(context_parts)


def format_response_with_highlighting(answer: str) -> str:
    """
    Apply markdown formatting to enhance readability.

    Enhancements:
    - Convert provision references to links: §922(a) → [§922(a)](/provision/...)

    Args:
        answer: LLM-generated answer

    Returns:
        Formatted answer with provision links
    """
    import re

    # Find provision references like "§922(a)" or "§922(d)(1)"
    pattern = r'§(\d+)\(([a-zA-Z0-9/]+)\)'

    def replace_with_link(match):
        section = match.group(1)
        subsection = match.group(2)
        provision_id = f"/us/usc/t18/s{section}/{subsection}"
        return f'[§{section}({subsection})]({provision_id})'

    formatted = re.sub(pattern, replace_with_link, answer)

    return formatted


def generate_rag_response(query: str, context_results: List[Dict[str, Any]]) -> str:
    """
    Generate LLM response using RAG context.

    Args:
        query: User query
        context_results: Retrieved context from hybrid search

    Returns:
        LLM-generated answer with citations and formatting
    """
    # Check if we have any results
    if not context_results or len(context_results) == 0:
        return "I don't have information about that in the firearms law database. The database contains provisions from 18 USC Chapter 44 (firearms regulations). Try asking about specific topics like licensing, prohibited persons, or interstate transport."

    # Prepare context with intelligent selection
    context = prepare_context_for_llm(context_results)

    # Generate response with OpenAI (with retry logic)
    system_prompt = """You are a legal research assistant for US firearms law (18 USC Ch. 44).

CRITICAL: Only answer using the provided context provisions below. If no provisions are provided, respond: "I don't have enough information to answer that question."

Answer concisely using the provided provisions. Follow these rules:
• Cite provisions: "According to §922(a)(1)..." or "§922(d) prohibits..."
• **Bold** key terms and critical requirements
• Quote exact statutory text when relevant
• If multiple provisions apply, cite all relevant sections
• Use clear sections for multi-part answers

Context provisions marked with [provision_num] for citation."""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"Context from legal provisions:\n\n{context}\n\nQuestion: {query}"
        }
    ]

    def _generate_completion():
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    answer = retry_with_backoff(_generate_completion)

    # Format response with provision links
    formatted_answer = format_response_with_highlighting(answer)

    return formatted_answer
