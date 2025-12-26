"""
pgvector loader: Bulk insert embeddings into PostgreSQL.
"""

import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    POSTGRES_USER, POSTGRES_PASSWORD
)

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
    psycopg2 = None


def get_connection():
    """Create PostgreSQL connection."""
    if not psycopg2:
        raise RuntimeError("psycopg2 not installed")

    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def load_embeddings_to_postgres(embeddings_data: List[Dict]) -> Dict[str, int]:
    """
    Bulk insert embeddings into PostgreSQL.

    Args:
        embeddings_data: List of dicts with provision_id, text, embedding, metadata

    Returns:
        Stats dict with inserted, errors counts
    """
    print(f"\n💾 Loading {len(embeddings_data)} embeddings to PostgreSQL\n")

    conn = get_connection()
    cur = conn.cursor()

    # Prepare data for bulk insert
    values = []
    for item in embeddings_data:
        values.append((
            item['provision_id'],
            item['section_num'],
            item['year'],
            item['provision_level'],
            item['provision_num'],
            item['text_content'],
            item.get('heading'),
            item['embedding'],  # pgvector handles list -> vector conversion
            item['has_references'],
            item['reference_count']
        ))

    # Bulk insert
    insert_query = """
        INSERT INTO provision_embeddings (
            provision_id, section_num, year,
            provision_level, provision_num,
            text_content, heading, embedding,
            has_references, reference_count
        ) VALUES %s
        ON CONFLICT (provision_id, year) DO UPDATE SET
            text_content = EXCLUDED.text_content,
            embedding = EXCLUDED.embedding,
            has_references = EXCLUDED.has_references,
            reference_count = EXCLUDED.reference_count
    """

    try:
        execute_values(cur, insert_query, values, page_size=100)
        conn.commit()

        inserted = cur.rowcount
        print(f"✅ Inserted/updated {inserted} embeddings")

        # Verify
        cur.execute("SELECT COUNT(*) FROM provision_embeddings")
        total = cur.fetchone()[0]
        print(f"📊 Total embeddings in database: {total}")

        stats = {
            'inserted': inserted,
            'total': total,
            'errors': 0
        }

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        stats = {
            'inserted': 0,
            'total': 0,
            'errors': 1
        }
        raise

    finally:
        cur.close()
        conn.close()

    return stats


def test_vector_search(query_text: str = "unlawful firearm sale", limit: int = 5):
    """
    Test semantic search with a sample query.

    Args:
        query_text: Text to search for
        limit: Number of results
    """
    from pipeline.gold.embed_provisions import embed_batch
    from openai import OpenAI
    from pipeline.config import OPENAI_API_KEY

    print(f"\n🔍 Testing semantic search: '{query_text}'\n")

    # Embed query
    client = OpenAI(api_key=OPENAI_API_KEY)
    query_embedding = embed_batch([query_text], client)[0]

    # Search
    conn = get_connection()
    cur = conn.cursor()

    search_query = """
        SELECT
            provision_id,
            section_num,
            year,
            provision_num,
            text_content,
            1 - (embedding <=> %s::vector) AS similarity
        FROM provision_embeddings
        WHERE year = 2024
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    cur.execute(search_query, (query_embedding, query_embedding, limit))
    results = cur.fetchall()

    print(f"Top {len(results)} results:\n")
    for i, (prov_id, section, year, num, text, sim) in enumerate(results, 1):
        print(f"{i}. § {section}{num} ({year}) - Similarity: {sim:.3f}")
        print(f"   {text[:150]}...\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    """Test pgvector loading."""

    from pipeline.gold.embed_provisions import embed_subsections_from_silver

    # Generate embeddings
    print("Step 1: Generating embeddings...")
    embeddings = embed_subsections_from_silver()

    # Load to database
    print("\nStep 2: Loading to PostgreSQL...")
    stats = load_embeddings_to_postgres(embeddings)

    # Test search
    if stats['inserted'] > 0:
        print("\nStep 3: Testing semantic search...")
        test_vector_search("unlawful firearm sale")

    print("\n✅ pgvector pipeline complete!")
