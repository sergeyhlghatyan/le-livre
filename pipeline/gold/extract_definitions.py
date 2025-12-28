"""
Definition Extraction Pipeline: Extract and link legal term definitions.

This script:
1. Identifies definition provisions in §921
2. Extracts defined terms using regex patterns
3. Finds usages across all provisions
4. Stores in PostgreSQL definition_usages table
5. Creates Neo4j USES_DEFINITION relationships

Usage:
    python pipeline/gold/extract_definitions.py
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
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


# Regex patterns for definition extraction
DEFINITION_PATTERNS = [
    r'[tT]he term ["\']([^"\']+)["\'] means',
    r'["\']([^"\']+)["\'] means',
    r'[aA]s used in this (?:section|chapter|title)[,\s]+["\']([^"\']+)["\']',
]


def get_postgres_connection():
    """Create PostgreSQL connection."""
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_section_provisions(section_num: str, year: int) -> List[Dict]:
    """
    Get all provisions for a specific section and year.

    Args:
        section_num: Section number (e.g., '921', '922')
        year: Year to fetch

    Returns:
        List of provisions with id, text, heading
    """
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provision_id, text_content, heading
        FROM provision_embeddings
        WHERE section_num = %s AND year = %s
        ORDER BY provision_id
    """, (section_num, year))

    provisions = []
    for row in cursor.fetchall():
        provisions.append({
            'provision_id': row[0],
            'text_content': row[1],
            'heading': row[2]
        })

    cursor.close()
    conn.close()

    return provisions


def get_all_provisions(year: int) -> List[Dict]:
    """
    Get all provisions for a specific year.

    Args:
        year: Year to fetch

    Returns:
        List of provisions with id and text
    """
    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provision_id, text_content
        FROM provision_embeddings
        WHERE year = %s
        ORDER BY provision_id
    """, (year,))

    provisions = []
    for row in cursor.fetchall():
        provisions.append({
            'provision_id': row[0],
            'text_content': row[1]
        })

    cursor.close()
    conn.close()

    return provisions


def extract_terms_from_text(text: str) -> List[str]:
    """
    Extract defined terms from provision text using regex patterns.

    Args:
        text: Provision text

    Returns:
        List of extracted terms
    """
    terms = []

    for pattern in DEFINITION_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            term = match.group(1)
            # Clean up the term
            term = term.strip()
            if term and len(term) > 2:  # Ignore very short terms
                terms.append(term)

    return terms


def extract_definitions(section_num: str = '921', year: int = 2024) -> Dict[str, str]:
    """
    Extract all definitions from a section (default §921).

    Args:
        section_num: Section containing definitions (default '921')
        year: Year to extract from (default 2024)

    Returns:
        Dict mapping term -> provision_id
    """
    print(f"\n📖 Extracting definitions from §{section_num} ({year})...\n")

    provisions = get_section_provisions(section_num, year)
    definitions = {}

    for prov in provisions:
        text = prov['text_content']
        terms = extract_terms_from_text(text)

        for term in terms:
            definitions[term] = prov['provision_id']
            print(f"  Found: '{term}' in {prov['provision_id']}")

    print(f"\n✅ Extracted {len(definitions)} definitions\n")

    return definitions


def find_definition_usages(definitions: Dict[str, str], year: int = 2024) -> List[Dict]:
    """
    Find usages of defined terms across all provisions.

    Args:
        definitions: Dict mapping term -> definition provision_id
        year: Year to search in (default 2024)

    Returns:
        List of usage records
    """
    print(f"\n🔍 Finding definition usages across all provisions...\n")

    all_provisions = get_all_provisions(year)
    usages = []

    total_provisions = len(all_provisions)

    for idx, prov in enumerate(all_provisions, 1):
        # Progress indicator
        if idx % 100 == 0 or idx == total_provisions:
            print(f"  Progress: {idx}/{total_provisions} provisions...")

        source_id = prov['provision_id']
        text = prov['text_content'].lower()

        for term, definition_id in definitions.items():
            # Skip if this IS the definition
            if source_id == definition_id:
                continue

            # Check if term is used in the text
            term_lower = term.lower()

            if term_lower in text:
                # Calculate confidence based on match type
                confidence = 1.0  # Exact case-insensitive match

                # Check for exact case match (higher confidence)
                if term in prov['text_content']:
                    confidence = 1.0

                usages.append({
                    'source_provision_id': source_id,
                    'source_year': year,
                    'definition_provision_id': definition_id,
                    'definition_year': year,
                    'term': term,
                    'confidence': confidence,
                    'detection_method': 'regex'
                })

    print(f"\n✅ Found {len(usages)} definition usages\n")

    return usages


def store_definition_usages(usages: List[Dict]):
    """
    Store definition usages in PostgreSQL.

    Args:
        usages: List of usage records
    """
    if not usages:
        print("⚠️  No usages to store")
        return

    print(f"💾 Storing {len(usages)} definition usages in PostgreSQL...\n")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    # Insert usages (ON CONFLICT DO NOTHING for idempotency)
    insert_query = """
        INSERT INTO definition_usages (
            source_provision_id, source_year,
            definition_provision_id, definition_year,
            term, confidence, detection_method
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_provision_id, source_year, definition_provision_id, term)
        DO NOTHING
    """

    for usage in usages:
        cursor.execute(insert_query, (
            usage['source_provision_id'],
            usage['source_year'],
            usage['definition_provision_id'],
            usage['definition_year'],
            usage['term'],
            usage['confidence'],
            usage['detection_method']
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Definition usages stored in PostgreSQL\n")


def create_definition_relationships(usages: List[Dict], batch_size: int = 100):
    """
    Create USES_DEFINITION relationships in Neo4j.

    Args:
        usages: List of usage records
        batch_size: Batch size for bulk operations
    """
    if not usages:
        print("⚠️  No usages to create relationships for")
        return

    print(f"📊 Creating USES_DEFINITION relationships in Neo4j...\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Deduplicate: only one relationship per source-target pair
    # (even if multiple terms are used)
    unique_pairs = {}
    for usage in usages:
        key = (usage['source_provision_id'], usage['definition_provision_id'], usage['source_year'])
        if key not in unique_pairs:
            unique_pairs[key] = usage
        else:
            # If duplicate, keep the one with higher confidence
            if usage['confidence'] > unique_pairs[key]['confidence']:
                unique_pairs[key] = usage

    unique_usages = list(unique_pairs.values())

    # Create relationships in batches
    total_batches = (len(unique_usages) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(unique_usages))
        batch = unique_usages[start_idx:end_idx]

        # Build relationship data for this batch
        rels = []
        for usage in batch:
            rels.append({
                'source_id': usage['source_provision_id'],
                'target_id': usage['definition_provision_id'],
                'year': usage['source_year'],
                'term': usage['term'],
                'confidence': usage['confidence']
            })

        # Cypher query to create relationships
        query = """
            UNWIND $rels AS rel
            MATCH (source:Provision {id: rel.source_id, year: rel.year})
            MATCH (target:Provision {id: rel.target_id, year: rel.year})
            MERGE (source)-[u:USES_DEFINITION]->(target)
            SET u.term = rel.term,
                u.confidence = rel.confidence
        """

        with driver.session() as session:
            session.run(query, rels=rels)

        print(f"  Batch {batch_idx + 1}/{total_batches}: {len(batch)} relationships created")

    driver.close()

    print(f"\n✅ All USES_DEFINITION relationships created\n")


def print_definition_summary(definitions: Dict[str, str], usages: List[Dict]):
    """Print summary statistics about extracted definitions."""
    print("\n" + "="*60)
    print("DEFINITION EXTRACTION SUMMARY")
    print("="*60)

    print(f"\nTotal definitions extracted: {len(definitions)}")
    print(f"Total usages found: {len(usages)}")

    # Count usages per term
    usage_counts = defaultdict(int)
    for usage in usages:
        usage_counts[usage['term']] += 1

    print("\nTop 10 most used terms:")
    sorted_terms = sorted(usage_counts.items(), key=lambda x: x[1], reverse=True)
    for term, count in sorted_terms[:10]:
        print(f"  '{term}': {count} usages")

    # Sample some definitions
    print("\nSample definitions:")
    for idx, (term, prov_id) in enumerate(list(definitions.items())[:5], 1):
        print(f"  {idx}. '{term}' defined in {prov_id}")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    """Run definition extraction pipeline."""

    if not psycopg or not GraphDatabase:
        print("❌ Missing required dependencies")
        sys.exit(1)

    print("\n" + "="*60)
    print("DEFINITION EXTRACTION PIPELINE")
    print("="*60)

    # Extract definitions from §921
    definitions = extract_definitions(section_num='921', year=2024)

    if not definitions:
        print("⚠️  No definitions found. Exiting.")
        sys.exit(0)

    # Find usages across all provisions
    usages = find_definition_usages(definitions, year=2024)

    # Print summary
    print_definition_summary(definitions, usages)

    # Store in PostgreSQL
    store_definition_usages(usages)

    # Create Neo4j relationships
    if usages:
        create_definition_relationships(usages)

    print("✅ Definition extraction pipeline complete!\n")
