"""
Semantic Similarity Pipeline: Compute and link semantically similar provisions.

This script:
1. Fetches all embeddings from PostgreSQL
2. Computes pairwise cosine similarity
3. Filters by threshold (default 0.75)
4. Keeps top K similar provisions per provision (default 10)
5. Creates Neo4j SEMANTICALLY_SIMILAR relationships

Usage:
    python pipeline/gold/compute_similarity.py [--year 2024] [--threshold 0.75] [--top-k 10]
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict

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

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("⚠️  numpy and scikit-learn required. Run: pip install numpy scikit-learn")
    np = None
    cosine_similarity = None


def get_postgres_connection():
    """Create PostgreSQL connection."""
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_all_embeddings(year: int) -> tuple:
    """
    Fetch all provision embeddings for a specific year.

    Args:
        year: Year to fetch embeddings for

    Returns:
        Tuple of (provision_ids, embeddings_matrix)
    """
    print(f"\n📥 Fetching embeddings for year {year}...\n")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provision_id, embedding
        FROM provision_embeddings
        WHERE year = %s AND embedding IS NOT NULL
        ORDER BY provision_id
    """, (year,))

    provision_ids = []
    embeddings_list = []

    for row in cursor.fetchall():
        provision_ids.append(row[0])
        # pgvector returns embeddings as lists or strings, parse if needed
        embedding = row[1]
        if isinstance(embedding, (str, bytes)):
            # Convert to string and strip any numpy string wrapper
            embedding_str = str(embedding)
            # Remove "np.str_(" and trailing ")"
            if embedding_str.startswith("np.str_('"):
                embedding_str = embedding_str[9:-2]  # Remove "np.str_('" and "')"
            # Remove leading/trailing quotes if present
            embedding_str = embedding_str.strip("'\"")
            # Parse as JSON array
            import json
            embedding = json.loads(embedding_str)
        embeddings_list.append(embedding)

    cursor.close()
    conn.close()

    # Convert to numpy array
    embeddings_matrix = np.array(embeddings_list)

    print(f"✅ Fetched {len(provision_ids)} provision embeddings")
    if embeddings_matrix.ndim > 1:
        print(f"   Embedding dimension: {embeddings_matrix.shape[1]}\n")
    else:
        print(f"   Warning: Embeddings matrix is 1D, reshaping...\n")
        # If 1D, it means we only have 1 embedding, reshape to 2D
        embeddings_matrix = embeddings_matrix.reshape(1, -1)

    return provision_ids, embeddings_matrix


def compute_similarity_relationships(
    provision_ids: List[str],
    embeddings_matrix: np.ndarray,
    year: int,
    threshold: float = 0.75,
    top_k: int = 10
) -> List[Dict]:
    """
    Compute semantic similarity and generate relationship records.

    Args:
        provision_ids: List of provision IDs
        embeddings_matrix: Numpy array of embeddings (N x D)
        year: Year these provisions are from
        threshold: Minimum similarity threshold (0.0-1.0)
        top_k: Maximum number of similar provisions per provision

    Returns:
        List of similarity relationship records
    """
    print(f"🔍 Computing pairwise cosine similarities...\n")
    print(f"   Threshold: {threshold}")
    print(f"   Top K: {top_k}\n")

    # Compute similarity matrix (N x N)
    sim_matrix = cosine_similarity(embeddings_matrix)

    print(f"✅ Similarity matrix computed: {sim_matrix.shape}\n")

    # Generate relationships
    print("📊 Generating similarity relationships...\n")

    relationships = []

    for i, provision_id in enumerate(provision_ids):
        # Get similarities for this provision
        similarities = sim_matrix[i]

        # Get indices sorted by similarity (descending)
        # Exclude self (index i) by setting its similarity to -1
        similarities[i] = -1
        top_indices = np.argsort(similarities)[::-1]

        # Keep top K above threshold
        count = 0
        for j in top_indices:
            if count >= top_k:
                break

            score = similarities[j]
            if score < threshold:
                break

            relationships.append({
                'from_id': provision_id,
                'to_id': provision_ids[j],
                'year': year,
                'score': float(score)
            })

            count += 1

    print(f"✅ Generated {len(relationships)} similarity relationships\n")

    return relationships


def create_similarity_relationships(relationships: List[Dict], batch_size: int = 100):
    """
    Create SEMANTICALLY_SIMILAR relationships in Neo4j.

    Args:
        relationships: List of similarity relationship records
        batch_size: Batch size for bulk operations
    """
    if not relationships:
        print("⚠️  No similarity relationships to create")
        return

    print(f"📊 Creating SEMANTICALLY_SIMILAR relationships in Neo4j...\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Create relationships in batches
    total_batches = (len(relationships) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(relationships))
        batch = relationships[start_idx:end_idx]

        # Cypher query to create relationships
        query = """
            UNWIND $rels AS rel
            MATCH (source:Provision {id: rel.from_id, year: rel.year})
            MATCH (target:Provision {id: rel.to_id, year: rel.year})
            MERGE (source)-[s:SEMANTICALLY_SIMILAR]->(target)
            SET s.score = rel.score,
                s.embedding_model = 'text-embedding-3-small'
        """

        with driver.session() as session:
            session.run(query, rels=batch)

        print(f"  Batch {batch_idx + 1}/{total_batches}: {len(batch)} relationships created")

    driver.close()

    print(f"\n✅ All SEMANTICALLY_SIMILAR relationships created\n")


def print_similarity_summary(relationships: List[Dict], threshold: float):
    """Print summary statistics about similarity relationships."""
    print("\n" + "="*60)
    print("SEMANTIC SIMILARITY SUMMARY")
    print("="*60)

    print(f"\nTotal similarity relationships: {len(relationships)}")
    print(f"Similarity threshold: {threshold}")

    if relationships:
        # Calculate statistics
        scores = [r['score'] for r in relationships]
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)

        print(f"\nSimilarity scores:")
        print(f"  Average: {avg_score:.3f}")
        print(f"  Min: {min_score:.3f}")
        print(f"  Max: {max_score:.3f}")

        # Show distribution
        high_sim = sum(1 for s in scores if s >= 0.90)
        med_sim = sum(1 for s in scores if 0.80 <= s < 0.90)
        low_sim = sum(1 for s in scores if s < 0.80)

        print(f"\nScore distribution:")
        print(f"  High (≥0.90): {high_sim} ({high_sim/len(scores)*100:.1f}%)")
        print(f"  Medium (0.80-0.89): {med_sim} ({med_sim/len(scores)*100:.1f}%)")
        print(f"  Low (<0.80): {low_sim} ({low_sim/len(scores)*100:.1f}%)")

        # Sample high-similarity pairs
        print("\nSample high-similarity pairs (top 5):")
        sorted_rels = sorted(relationships, key=lambda x: x['score'], reverse=True)
        for rel in sorted_rels[:5]:
            print(f"  {rel['from_id']} ↔ {rel['to_id']}: {rel['score']:.3f}")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    """Run semantic similarity computation pipeline."""

    parser = argparse.ArgumentParser(description="Compute semantic similarity relationships")
    parser.add_argument('--year', type=int, default=2024, help='Year to compute similarities for')
    parser.add_argument('--threshold', type=float, default=0.75, help='Minimum similarity threshold (0-1)')
    parser.add_argument('--top-k', type=int, default=10, help='Maximum similar provisions per provision')
    args = parser.parse_args()

    if not psycopg or not GraphDatabase or not np or not cosine_similarity:
        print("❌ Missing required dependencies")
        sys.exit(1)

    print("\n" + "="*60)
    print("SEMANTIC SIMILARITY PIPELINE")
    print("="*60)

    # Fetch embeddings
    provision_ids, embeddings_matrix = get_all_embeddings(args.year)

    if len(provision_ids) == 0:
        print("⚠️  No embeddings found. Exiting.")
        sys.exit(0)

    # Compute similarities
    relationships = compute_similarity_relationships(
        provision_ids,
        embeddings_matrix,
        args.year,
        args.threshold,
        args.top_k
    )

    # Print summary
    print_similarity_summary(relationships, args.threshold)

    # Create Neo4j relationships
    if relationships:
        create_similarity_relationships(relationships)

    print("✅ Semantic similarity pipeline complete!\n")
