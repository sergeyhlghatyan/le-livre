"""Load embeddings from JSON to PostgreSQL."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def load_embeddings_from_json(embeddings_dir: Path = None):
    """Load all embedding JSON files."""
    if embeddings_dir is None:
        embeddings_dir = Path(__file__).parent.parent.parent / 'data' / 'gold' / 'embeddings'

    all_embeddings = []
    for json_file in sorted(embeddings_dir.glob('*.json')):
        if json_file.name == '.gitkeep':
            continue

        with open(json_file) as f:
            embeddings = json.load(f)

        all_embeddings.extend(embeddings)
        print(f"📄 Loaded {len(embeddings)} from {json_file.name}")

    print(f"\n✅ Loaded {len(all_embeddings)} total embeddings\n")
    return all_embeddings


def load_to_postgres(embeddings):
    """Bulk insert to PostgreSQL."""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

    cur = conn.cursor()

    # Deduplicate by (provision_id, year) - keep last occurrence
    seen = {}
    for item in embeddings:
        key = (item['provision_id'], item['metadata']['year'])
        seen[key] = item

    deduped = list(seen.values())
    if len(deduped) < len(embeddings):
        print(f"⚠️  Removed {len(embeddings) - len(deduped)} duplicates\n")

    # Prepare data
    values = [
        (
            item['provision_id'],
            item['metadata']['section_num'],
            item['metadata']['year'],
            item['metadata']['provision_level'],
            item['metadata']['provision_num'],
            item['text_content'],
            item['metadata'].get('heading'),
            item['embedding'],
            item['metadata']['has_references'],
            item['metadata']['reference_count']
        )
        for item in deduped
    ]

    # Bulk insert (idempotent)
    query = """
        INSERT INTO provision_embeddings (
            provision_id, section_num, year, provision_level, provision_num,
            text_content, heading, embedding, has_references, reference_count
        )
        VALUES %s
        ON CONFLICT (provision_id, year) DO UPDATE SET
            text_content = EXCLUDED.text_content,
            embedding = EXCLUDED.embedding,
            has_references = EXCLUDED.has_references,
            reference_count = EXCLUDED.reference_count
    """

    execute_values(cur, query, values, page_size=100)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM provision_embeddings")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"✅ Inserted {len(values)} embeddings")
    print(f"📊 Total in database: {total}\n")


if __name__ == "__main__":
    print("\n💾 Loading embeddings to PostgreSQL\n")

    embeddings = load_embeddings_from_json()
    load_to_postgres(embeddings)

    print("✅ Complete!")
