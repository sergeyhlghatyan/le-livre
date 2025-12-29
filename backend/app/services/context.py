"""
Provision Context Service: Rich context retrieval for provisions.

This service provides comprehensive context for a provision including:
- Timeline (available years)
- Relations (parent, children, references)
- Amendments (changes across years)
- Definitions (terms used and provided)
- Similar provisions (semantic similarity)
"""

from typing import Dict, List, Optional, Any
from ..database import get_postgres_conn, get_neo4j_driver


def get_provision_context(
    provision_id: str,
    year: int,
    include_timeline: bool = True,
    include_relations: bool = True,
    include_amendments: bool = True,
    include_definitions: bool = True,
    include_similar: bool = True
) -> Dict[str, Any]:
    """
    Fetch rich context for a provision in a single query.

    Args:
        provision_id: Provision ID (e.g., '/us/usc/t18/s922/d')
        year: Year to fetch context for
        include_timeline: Include available years
        include_relations: Include parent, children, references
        include_amendments: Include amendment history
        include_definitions: Include definition usages
        include_similar: Include semantically similar provisions

    Returns:
        Dict with provision context including all requested components
    """
    # Fetch base provision data (always included)
    provision = _get_base_provision(provision_id, year)

    if not provision:
        return None

    # Build context dict
    context = {
        'provision': provision
    }

    # Fetch optional components
    if include_timeline:
        context['timeline'] = _get_timeline(provision_id)

    if include_relations:
        context['relations'] = _get_relations(provision_id, year)

    if include_amendments:
        context['amendments'] = _get_amendments(provision_id)

    if include_definitions:
        context['definitions'] = _get_definitions(provision_id, year)

    if include_similar:
        context['similar'] = _get_similar_provisions(provision_id, year)

    return context


def _get_base_provision(provision_id: str, year: int) -> Optional[Dict]:
    """Fetch base provision data from PostgreSQL."""
    with get_postgres_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT provision_id, section_num, year, provision_level,
                       provision_num, text_content, heading
                FROM provision_embeddings
                WHERE provision_id = %s AND year = %s
            """, (provision_id, year))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'provision_id': row[0],
                'section_num': row[1],
                'year': row[2],
                'provision_level': row[3],
                'provision_num': row[4],
                'text_content': row[5],
                'heading': row[6]
            }


def _get_timeline(provision_id: str) -> List[int]:
    """Fetch all available years for a provision."""
    with get_postgres_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT year
                FROM provision_embeddings
                WHERE provision_id = %s
                ORDER BY year
            """, (provision_id,))

            rows = cursor.fetchall()
            return [row[0] for row in rows]


def _get_relations(provision_id: str, year: int) -> Dict[str, Any]:
    """Fetch all relationships for a provision from Neo4j."""
    driver = get_neo4j_driver()

    query = """
        MATCH (p:Provision {id: $provision_id, year: $year})

        OPTIONAL MATCH (parent:Provision)-[:PARENT_OF]->(p)
        OPTIONAL MATCH (p)-[:PARENT_OF]->(child:Provision)
        OPTIONAL MATCH (p)-[:REFERENCES]->(ref:Provision)
        OPTIONAL MATCH (incoming:Provision)-[:REFERENCES]->(p)

        RETURN p,
               parent,
               collect(DISTINCT child) as children,
               collect(DISTINCT ref) as references,
               collect(DISTINCT incoming) as referenced_by
    """

    with driver.session() as session:
        result = session.run(query, provision_id=provision_id, year=year)
        record = result.single()

        if not record:
            return {
                'parent': None,
                'children': [],
                'references': [],
                'referenced_by': []
            }

        # Convert Neo4j nodes to dicts with proper field mapping
        def node_to_dict(node):
            if node is None:
                return None

            # Map Neo4j property names to frontend expected names
            node_dict = dict(node)
            return {
                'provision_id': node_dict.get('id'),
                'section_num': node_dict.get('section_num'),
                'year': node_dict.get('year'),
                'provision_level': node_dict.get('level'),
                'provision_num': node_dict.get('num'),
                'text_content': node_dict.get('text', ''),
                'heading': node_dict.get('heading')
            }

        return {
            'parent': node_to_dict(record['parent']),
            'children': [node_to_dict(n) for n in record['children'] if n],
            'references': [node_to_dict(n) for n in record['references'] if n],
            'referenced_by': [node_to_dict(n) for n in record['referenced_by'] if n]
        }


def _get_amendments(provision_id: str) -> List[Dict]:
    """Fetch amendment history for a provision from Neo4j."""
    driver = get_neo4j_driver()

    query = """
        MATCH (new:Provision {id: $provision_id})-[a:AMENDED_FROM]->(old:Provision)
        RETURN old.year as year_old,
               new.year as year_new,
               a.change_type as change_type
        ORDER BY old.year
    """

    with driver.session() as session:
        result = session.run(query, provision_id=provision_id)

        amendments = []
        for record in result:
            amendments.append({
                'year_old': record['year_old'],
                'year_new': record['year_new'],
                'change_type': record['change_type']
            })

        return amendments


def _get_definitions(provision_id: str, year: int) -> Dict[str, Any]:
    """Fetch definition usages for a provision."""
    driver = get_neo4j_driver()

    # Get definitions this provision USES
    uses_query = """
        MATCH (p:Provision {id: $provision_id, year: $year})
              -[u:USES_DEFINITION]->(def:Provision)
        RETURN def.id as definition_id,
               u.term as term,
               u.confidence as confidence
    """

    # Get definitions this provision PROVIDES (if any)
    provides_query = """
        MATCH (user:Provision)-[u:USES_DEFINITION]->
              (p:Provision {id: $provision_id, year: $year})
        RETURN user.id as user_id,
               u.term as term,
               count(user) as usage_count
    """

    with driver.session() as session:
        # Fetch uses
        uses_result = session.run(uses_query, provision_id=provision_id, year=year)
        uses = []
        for record in uses_result:
            uses.append({
                'definition_id': record['definition_id'],
                'term': record['term'],
                'confidence': record['confidence']
            })

        # Fetch provides
        provides_result = session.run(provides_query, provision_id=provision_id, year=year)
        provides = []
        for record in provides_result:
            provides.append({
                'term': record['term'],
                'usage_count': record['usage_count']
            })

        return {
            'uses': uses,
            'provides': provides
        }


def _get_similar_provisions(provision_id: str, year: int, limit: int = 10) -> List[Dict]:
    """Fetch semantically similar provisions from Neo4j."""
    driver = get_neo4j_driver()

    query = """
        MATCH (p:Provision {id: $provision_id, year: $year})
              -[s:SEMANTICALLY_SIMILAR]->(sim:Provision)
        WHERE sim.year = $year
        RETURN sim.id as provision_id,
               sim.text as text,
               sim.heading as heading,
               s.score as similarity_score
        ORDER BY s.score DESC
        LIMIT $limit
    """

    with driver.session() as session:
        result = session.run(query,
                             provision_id=provision_id,
                             year=year,
                             limit=limit)

        similar = []
        for record in result:
            similar.append({
                'provision_id': record['provision_id'],
                'heading': record['heading'],
                'text_content': record['text'],
                'similarity_score': record['similarity_score']
            })

        return similar
