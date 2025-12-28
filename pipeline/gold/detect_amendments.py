"""
Amendment Detection Pipeline: Detect and track provision changes across years.

This script:
1. Compares provisions across consecutive years
2. Classifies changes (added, modified, removed, renumbered)
3. Creates Neo4j AMENDED_FROM relationships

Usage:
    python pipeline/gold/detect_amendments.py
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
from pipeline.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

try:
    import psycopg
except ImportError:
    print("⚠️  psycopg not installed. Run: pip install psycopg")
    psycopg = None

try:
    from neo4j import GraphDatabase
except ImportError:
    print("⚠️  neo4j driver not installed. Run: pip install neo4j")
    GraphDatabase = None


def get_postgres_connection():
    """Create PostgreSQL connection."""
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_all_provision_ids() -> List[str]:
    """Get all unique provision IDs."""
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT provision_id
        FROM provision_embeddings
        ORDER BY provision_id
    """)

    provision_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return provision_ids


def get_years_for_provision(provision_id: str) -> List[int]:
    """Get all years a provision exists."""
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT year
        FROM provision_embeddings
        WHERE provision_id = %s
        ORDER BY year
    """, (provision_id,))

    years = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return years


def get_provision_text(provision_id: str, year: int) -> str:
    """Get provision text for a specific year."""
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text_content
        FROM provision_embeddings
        WHERE provision_id = %s AND year = %s
    """, (provision_id, year))

    result = cursor.fetchone()
    text = result[0] if result else ""

    cursor.close()
    conn.close()

    return text


def classify_change(old_text: str, new_text: str, similarity_ratio: float) -> str:
    """
    Classify the type of change between two provision versions.

    Args:
        old_text: Previous version text
        new_text: New version text
        similarity_ratio: Text similarity ratio (0.0-1.0)

    Returns:
        Change type: 'added', 'removed', 'modified', 'renumbered', or 'unchanged'
    """
    if not old_text and new_text:
        return 'added'
    elif old_text and not new_text:
        return 'removed'
    elif similarity_ratio == 1.0:
        return 'unchanged'
    elif similarity_ratio >= 0.95:
        # Very similar text - likely minor modification or renumbering
        return 'modified'
    else:
        # Substantive change
        return 'modified'


def detect_amendments() -> List[Dict]:
    """
    Detect all amendments by comparing provisions across years.

    Returns:
        List of amendment records with:
        - provision_id
        - year_old
        - year_new
        - change_type
        - similarity_ratio
    """
    print("\n🔍 Detecting amendments across all provisions...\n")

    provision_ids = get_all_provision_ids()
    amendments = []

    total_provisions = len(provision_ids)

    for idx, provision_id in enumerate(provision_ids, 1):
        # Progress indicator
        if idx % 100 == 0 or idx == total_provisions:
            print(f"  Progress: {idx}/{total_provisions} provisions...")

        # Get all years this provision exists
        years = get_years_for_provision(provision_id)

        if len(years) < 2:
            # Provision exists in only one year, no amendments to detect
            continue

        # Compare consecutive years
        for i in range(len(years) - 1):
            old_year = years[i]
            new_year = years[i + 1]

            old_text = get_provision_text(provision_id, old_year)
            new_text = get_provision_text(provision_id, new_year)

            # Calculate text similarity
            similarity_ratio = SequenceMatcher(None, old_text, new_text).ratio()

            # Classify change
            change_type = classify_change(old_text, new_text, similarity_ratio)

            if change_type != 'unchanged':
                amendments.append({
                    'provision_id': provision_id,
                    'year_old': old_year,
                    'year_new': new_year,
                    'change_type': change_type,
                    'similarity_ratio': similarity_ratio
                })

    print(f"\n✅ Detected {len(amendments)} amendments\n")

    return amendments


def create_amendment_relationships(amendments: List[Dict], batch_size: int = 100):
    """
    Create AMENDED_FROM relationships in Neo4j.

    Args:
        amendments: List of amendment records
        batch_size: Batch size for bulk operations
    """
    if not amendments:
        print("⚠️  No amendments to create relationships for")
        return

    print(f"📊 Creating AMENDED_FROM relationships in Neo4j...\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Create relationships in batches
    total_batches = (len(amendments) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(amendments))
        batch = amendments[start_idx:end_idx]

        # Build relationship data for this batch
        rels = []
        for amendment in batch:
            rels.append({
                'provision_id': amendment['provision_id'],
                'year_old': amendment['year_old'],
                'year_new': amendment['year_new'],
                'change_type': amendment['change_type']
            })

        # Cypher query to create relationships
        query = """
            UNWIND $rels AS rel
            MATCH (old:Provision {id: rel.provision_id, year: rel.year_old})
            MATCH (new:Provision {id: rel.provision_id, year: rel.year_new})
            MERGE (new)-[a:AMENDED_FROM]->(old)
            SET a.change_type = rel.change_type
        """

        with driver.session() as session:
            session.run(query, rels=rels)

        print(f"  Batch {batch_idx + 1}/{total_batches}: {len(batch)} relationships created")

    driver.close()

    print(f"\n✅ All AMENDED_FROM relationships created\n")


def print_amendment_summary(amendments: List[Dict]):
    """Print summary statistics about detected amendments."""
    print("\n" + "="*60)
    print("AMENDMENT DETECTION SUMMARY")
    print("="*60)

    # Count by change type
    change_counts = defaultdict(int)
    for amendment in amendments:
        change_counts[amendment['change_type']] += 1

    print(f"\nTotal amendments: {len(amendments)}")
    print("\nBy change type:")
    for change_type in ['added', 'modified', 'removed', 'renumbered']:
        count = change_counts.get(change_type, 0)
        print(f"  {change_type:12s}: {count}")

    # Sample some modifications
    modifications = [a for a in amendments if a['change_type'] == 'modified']
    if modifications:
        print("\nSample modifications (showing first 5):")
        for amendment in modifications[:5]:
            print(f"  {amendment['provision_id']}: {amendment['year_old']} → {amendment['year_new']} "
                  f"(similarity: {amendment['similarity_ratio']:.2%})")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    """Run amendment detection pipeline."""

    if not psycopg or not GraphDatabase:
        print("❌ Missing required dependencies")
        sys.exit(1)

    print("\n" + "="*60)
    print("AMENDMENT DETECTION PIPELINE")
    print("="*60)

    # Detect amendments
    amendments = detect_amendments()

    # Print summary
    print_amendment_summary(amendments)

    # Create Neo4j relationships
    if amendments:
        create_amendment_relationships(amendments)

    print("✅ Amendment detection pipeline complete!\n")
