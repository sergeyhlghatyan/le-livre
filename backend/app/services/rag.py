"""RAG service for semantic and graph-based search."""
from typing import List, Dict, Any
import openai
from ..database import get_postgres_conn, get_neo4j_driver
from ..config import get_settings

settings = get_settings()
openai.api_key = settings.openai_api_key


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a text query."""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


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
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cur.execute(sql, (query_embedding, year, query_embedding, limit))
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
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cur.execute(sql, (query_embedding, query_embedding, limit))

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


def graph_search(provision_id: str, year: int, relationship_type: str = None) -> List[Dict[str, Any]]:
    """
    Graph-based search using Neo4j relationships.

    Args:
        provision_id: Starting provision ID
        year: Year to search
        relationship_type: Optional relationship filter (CONTAINS, REFERENCES)

    Returns:
        List of related provisions
    """
    driver = get_neo4j_driver()

    with driver.session(database=settings.neo4j_database) as session:
        if relationship_type:
            query = """
            MATCH (p:Provision {provision_id: $provision_id, year: $year})
            MATCH (p)-[r]->(related:Provision)
            WHERE type(r) = $rel_type
            RETURN related.provision_id as provision_id,
                   related.section_num as section_num,
                   related.year as year,
                   related.provision_level as provision_level,
                   related.provision_num as provision_num,
                   related.text_content as text_content,
                   related.heading as heading,
                   type(r) as relationship
            LIMIT 10
            """
            result = session.run(query, provision_id=provision_id, year=year, rel_type=relationship_type)
        else:
            query = """
            MATCH (p:Provision {provision_id: $provision_id, year: $year})
            MATCH (p)-[r]->(related:Provision)
            RETURN related.provision_id as provision_id,
                   related.section_num as section_num,
                   related.year as year,
                   related.provision_level as provision_level,
                   related.provision_num as provision_num,
                   related.text_content as text_content,
                   related.heading as heading,
                   type(r) as relationship
            LIMIT 10
            """
            result = session.run(query, provision_id=provision_id, year=year)

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


def hybrid_search(query: str, limit: int = 10, year: int = None) -> Dict[str, Any]:
    """
    Hybrid search combining semantic and graph-based results.

    Args:
        query: Search query
        limit: Total number of results
        year: Optional year filter

    Returns:
        Combined results from semantic and graph search
    """
    # Get semantic results
    semantic_results = semantic_search(query, limit=limit, year=year)

    # Get graph results for top semantic match
    graph_results = []
    if semantic_results:
        top_match = semantic_results[0]
        graph_results = graph_search(
            provision_id=top_match["provision_id"],
            year=top_match["year"]
        )

    # Deduplicate and combine
    seen = set()
    combined = []

    for result in semantic_results:
        key = (result["provision_id"], result["year"])
        if key not in seen:
            seen.add(key)
            combined.append(result)

    for result in graph_results:
        key = (result["provision_id"], result["year"])
        if key not in seen:
            seen.add(key)
            combined.append(result)

    return {
        "query": query,
        "semantic_count": len(semantic_results),
        "graph_count": len(graph_results),
        "total_results": len(combined),
        "results": combined[:limit]
    }


def generate_rag_response(query: str, context_results: List[Dict[str, Any]]) -> str:
    """
    Generate LLM response using RAG context.

    Args:
        query: User query
        context_results: Retrieved context from hybrid search

    Returns:
        LLM-generated answer
    """
    # Build context from results
    context_parts = []
    for i, result in enumerate(context_results, 1):
        heading = result.get("heading", "")
        text = result["text_content"]
        year = result["year"]
        provision_id = result["provision_id"]

        context_parts.append(
            f"[{i}] {heading} ({provision_id}, {year})\n{text}"
        )

    context = "\n\n".join(context_parts)

    # Generate response with OpenAI
    messages = [
        {
            "role": "system",
            "content": "You are a legal assistant specializing in US firearms law (Title 18 USC). "
                      "Answer questions based on the provided legal provisions. "
                      "Cite specific provision IDs when referencing the law."
        },
        {
            "role": "user",
            "content": f"Context from legal provisions:\n\n{context}\n\nQuestion: {query}"
        }
    ]

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content
