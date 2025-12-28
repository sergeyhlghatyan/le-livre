"""
Neo4j graph loader: Load sections, provisions, and references into graph database.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.models.silver import SectionVersion, Provision, ReferenceRecord
from pipeline.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, SILVER_SECTIONS_DIR, SILVER_REFS_DIR

try:
    from neo4j import GraphDatabase
except ImportError:
    print("⚠️  neo4j driver not installed. Run: pip install neo4j")
    GraphDatabase = None


class GraphLoader:
    def __init__(self, uri: str, user: str, password: str):
        if not GraphDatabase:
            raise RuntimeError("neo4j driver not installed")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_section_node(self, section: SectionVersion):
        """Create Section node."""
        query = """
            MERGE (s:Section {id: $id, year: $year})
            SET s.section_num = $section_num,
                s.title = $title,
                s.heading = $heading,
                s.provision_count = $provision_count,
                s.reference_count = $reference_count
        """

        with self.driver.session() as session:
            session.run(query,
                id=section.id,
                year=section.year,
                section_num=section.section_num,
                title=section.title_num,
                heading=section.heading,
                provision_count=section.provision_count,
                reference_count=section.reference_count
            )

    def create_provision_nodes_batch(self, provisions: List[Dict]):
        """Create provision nodes in batch."""
        query = """
            UNWIND $provisions AS prov
            MERGE (p:Provision {id: prov.id, year: prov.year})
            SET p.level = prov.level,
                p.num = prov.num,
                p.text = prov.text,
                p.heading = prov.heading,
                p.section_num = prov.section_num
        """

        with self.driver.session() as session:
            session.run(query, provisions=provisions)

    def create_relationships_batch(self, relationships: List[Dict], rel_type: str):
        """Create relationships in batch."""
        if rel_type == "CONTAINS":
            query = """
                UNWIND $rels AS rel
                MATCH (s:Section {id: rel.from_id, year: rel.year})
                MATCH (p:Provision {id: rel.to_id, year: rel.year})
                MERGE (s)-[:CONTAINS]->(p)
            """
        elif rel_type == "PARENT_OF":
            query = """
                UNWIND $rels AS rel
                MATCH (parent:Provision {id: rel.from_id, year: rel.year})
                MATCH (child:Provision {id: rel.to_id, year: rel.year})
                MERGE (parent)-[:PARENT_OF]->(child)
            """
        elif rel_type == "REFERENCES":
            query = """
                UNWIND $rels AS rel
                MATCH (source:Provision {id: rel.from_id, year: rel.year})
                MERGE (target:Provision {id: rel.to_id})
                MERGE (source)-[r:REFERENCES]->(target)
                SET r.display_text = rel.display_text,
                    r.year = rel.year
            """

        with self.driver.session() as session:
            session.run(query, rels=relationships)

    def flatten_provisions(self, section: SectionVersion) -> tuple:
        """Flatten section into provisions list and relationships."""
        provisions = []
        contains_rels = []
        parent_of_rels = []

        def process_provision(prov: Provision, parent_id: str = None):
            # Add provision
            provisions.append({
                'id': prov.id,
                'year': section.year,
                'level': prov.tag,
                'num': prov.num,
                'text': prov.text or '',
                'heading': prov.heading,
                'section_num': section.section_num
            })

            # Add relationship
            if parent_id:
                parent_of_rels.append({
                    'from_id': parent_id,
                    'to_id': prov.id,
                    'year': section.year
                })
            else:
                # Root provision -> CONTAINS
                contains_rels.append({
                    'from_id': section.id,
                    'to_id': prov.id,
                    'year': section.year
                })

            # Recurse children
            for child_list in [prov.subsections, prov.paragraphs, prov.subparagraphs, prov.clauses, prov.subclauses]:
                for child in child_list:
                    process_provision(child, prov.id)

        # Process all subsections
        for subsection in section.subsections:
            process_provision(subsection)

        return provisions, contains_rels, parent_of_rels


def load_sections_to_graph(
    sections_dir: Path = None,
    refs_dir: Path = None,
    batch_size: int = 100
) -> Dict[str, int]:
    """
    Load sections and references to Neo4j.

    Args:
        sections_dir: Silver sections directory
        refs_dir: Silver references directory
        batch_size: Batch size for bulk operations

    Returns:
        Stats dict
    """
    if sections_dir is None:
        sections_dir = SILVER_SECTIONS_DIR
    if refs_dir is None:
        refs_dir = SILVER_REFS_DIR

    loader = GraphLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    print(f"\n🔗 Loading sections to Neo4j\n")

    stats = {
        'sections': 0,
        'provisions': 0,
        'contains': 0,
        'parent_of': 0,
        'references': 0
    }

    # Load sections
    section_dirs = sorted([d for d in sections_dir.iterdir() if d.is_dir()])

    for section_dir in section_dirs:
        section_num = section_dir.name
        print(f"📄 Section {section_num}:")

        for json_file in sorted(section_dir.glob('*.json')):
            year = int(json_file.stem)

            with open(json_file, 'r') as f:
                data = json.load(f)

            section = SectionVersion(**data)

            # Create section node
            loader.create_section_node(section)
            stats['sections'] += 1

            # Flatten provisions
            provisions, contains, parent_of = loader.flatten_provisions(section)

            # Create provision nodes (batch)
            loader.create_provision_nodes_batch(provisions)
            stats['provisions'] += len(provisions)

            # Create CONTAINS relationships
            loader.create_relationships_batch(contains, "CONTAINS")
            stats['contains'] += len(contains)

            # Create PARENT_OF relationships (batch)
            for i in range(0, len(parent_of), batch_size):
                batch = parent_of[i:i + batch_size]
                loader.create_relationships_batch(batch, "PARENT_OF")
            stats['parent_of'] += len(parent_of)

            print(f"  {year}: {len(provisions)} provisions, {len(parent_of)} hierarchy edges")

    # Load references
    print(f"\n🔗 Loading references:")

    for jsonl_file in sorted(refs_dir.glob('*.jsonl')):
        year = int(jsonl_file.stem)
        refs = []

        with open(jsonl_file, 'r') as f:
            for line in f:
                ref_data = json.loads(line)
                refs.append({
                    'from_id': ref_data['source_provision_id'],
                    'to_id': ref_data['target_provision_id'],
                    'display_text': ref_data['display_text'],
                    'year': ref_data['year']
                })

        if refs:
            loader.create_relationships_batch(refs, "REFERENCES")
            stats['references'] += len(refs)
            print(f"  {year}: {len(refs)} references")

    loader.close()

    print(f"\n{'='*60}")
    print(f"✅ Loaded to Neo4j:")
    print(f"   Sections: {stats['sections']}")
    print(f"   Provisions: {stats['provisions']}")
    print(f"   CONTAINS edges: {stats['contains']}")
    print(f"   PARENT_OF edges: {stats['parent_of']}")
    print(f"   REFERENCES edges: {stats['references']}")
    print(f"{'='*60}\n")

    return stats


def test_graph_queries():
    """Run sample graph queries."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print("\n🔍 Testing graph queries:\n")

    with driver.session() as session:
        # Query 1: Count nodes
        result = session.run("MATCH (n) RETURN labels(n)[0] AS type, count(*) AS count")
        print("Node counts:")
        for record in result:
            print(f"  {record['type']}: {record['count']}")

        # Query 2: Find references from section 922
        result = session.run("""
            MATCH (s:Section {section_num: '922', year: 2024})-[:CONTAINS*]->(p:Provision)
            MATCH (p)-[r:REFERENCES]->(target)
            RETURN p.id, r.display_text, target.id
            LIMIT 5
        """)
        print("\nSample references from §922 (2024):")
        for record in result:
            print(f"  {record['p.id']} -> {record['target.id']}: {record['r.display_text']}")

    driver.close()


def run_phase0_enrichment():
    """
    Run Phase 0 enrichment pipelines to create new relationships.

    This function orchestrates:
    1. Amendment detection (AMENDED_FROM relationships)
    2. Definition extraction (USES_DEFINITION relationships)
    3. Semantic similarity (SEMANTICALLY_SIMILAR relationships)
    """
    import subprocess
    import sys

    print("\n" + "="*60)
    print("PHASE 0 ENRICHMENT PIPELINE")
    print("="*60 + "\n")

    # Get the pipeline directory
    pipeline_dir = Path(__file__).parent

    # 1. Detect amendments
    print("\n[1/3] Running amendment detection...\n")
    result = subprocess.run(
        [sys.executable, str(pipeline_dir / "detect_amendments.py")],
        capture_output=False
    )
    if result.returncode != 0:
        print("⚠️  Amendment detection failed")
    else:
        print("✅ Amendment detection complete\n")

    # 2. Extract definitions
    print("\n[2/3] Running definition extraction...\n")
    result = subprocess.run(
        [sys.executable, str(pipeline_dir / "extract_definitions.py")],
        capture_output=False
    )
    if result.returncode != 0:
        print("⚠️  Definition extraction failed")
    else:
        print("✅ Definition extraction complete\n")

    # 3. Compute similarity
    print("\n[3/3] Running semantic similarity computation...\n")
    result = subprocess.run(
        [sys.executable, str(pipeline_dir / "compute_similarity.py")],
        capture_output=False
    )
    if result.returncode != 0:
        print("⚠️  Similarity computation failed")
    else:
        print("✅ Similarity computation complete\n")

    print("\n" + "="*60)
    print("PHASE 0 ENRICHMENT COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    """Test Neo4j loading."""

    stats = load_sections_to_graph()

    if stats['provisions'] > 0:
        test_graph_queries()

    print("\n✅ Neo4j pipeline complete!")

    # Optionally run Phase 0 enrichment
    import sys
    if "--phase0" in sys.argv:
        run_phase0_enrichment()
