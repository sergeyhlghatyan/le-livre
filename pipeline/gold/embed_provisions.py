"""
Embedding pipeline: Extract subsections and generate embeddings.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.models.silver import SectionVersion, Provision
from pipeline.config import OPENAI_API_KEY, SILVER_SECTIONS_DIR

try:
    from openai import OpenAI
except ImportError:
    print("⚠️  OpenAI not installed. Run: pip install openai")
    OpenAI = None


def flatten_all_provisions(section: SectionVersion) -> List[Tuple[str, str, Dict]]:
    """
    Recursively extract ALL provisions from a section at all hierarchy levels.

    Extracts: subsections, paragraphs, subparagraphs, clauses, subclauses

    Args:
        section: Validated SectionVersion

    Returns:
        List of (provision_id, formatted_text, metadata) tuples
    """
    all_provisions = []

    def extract_provision(
        prov: Provision,
        level: str,
        section_num: str,
        section_heading: str,
        year: int,
        parent_id: str = None
    ) -> List[Tuple[str, str, Dict]]:
        """Recursively extract a provision and all its children."""
        provisions = []

        # Format text with context
        text_parts = []

        if section_heading:
            text_parts.append(section_heading.strip())

        text_parts.append(f"§ {section_num}")
        text_parts.append(prov.num)

        if prov.heading:
            text_parts.append(prov.heading.strip())

        if prov.text:
            text_parts.append(prov.text.strip())

        formatted_text = " ".join(text_parts)

        # Metadata
        metadata = {
            'section_num': section_num,
            'year': year,
            'provision_level': level,
            'provision_num': prov.num,
            'heading': prov.heading,
            'has_references': len(prov.refs) > 0,
            'reference_count': len(prov.refs),
            'parent_id': parent_id
        }

        provisions.append((prov.id, formatted_text, metadata))

        # Recursively extract children
        child_map = {
            'subsection': ('paragraph', prov.paragraphs),
            'paragraph': ('subparagraph', prov.subparagraphs),
            'subparagraph': ('clause', prov.clauses),
            'clause': ('subclause', prov.subclauses),
            'subclause': (None, [])
        }

        child_level, children = child_map.get(level, (None, []))

        if child_level and children:
            for child in children:
                provisions.extend(extract_provision(
                    child,
                    child_level,
                    section_num,
                    section_heading,
                    year,
                    parent_id=prov.id
                ))

        return provisions

    # Extract all subsections and their nested children
    for subsection in section.subsections:
        all_provisions.extend(extract_provision(
            subsection,
            'subsection',
            section.section_num,
            section.heading,
            section.year
        ))

    return all_provisions


def extract_subsections(section: SectionVersion) -> List[Tuple[str, str, Dict]]:
    """
    Extract ONLY subsections from a section (legacy function for compatibility).

    Args:
        section: Validated SectionVersion

    Returns:
        List of (provision_id, formatted_text, metadata) tuples
    """
    subsections = []

    for subsection in section.subsections:
        # Format text with context
        # "{heading} § {section_num} {subsection_num} {text}"
        text_parts = []

        if section.heading:
            text_parts.append(section.heading.strip())

        text_parts.append(f"§ {section.section_num}")
        text_parts.append(subsection.num)

        if subsection.text:
            text_parts.append(subsection.text.strip())

        # Add child provision summaries if available
        if subsection.paragraphs:
            child_texts = [p.text[:200].strip() for p in subsection.paragraphs[:3] if p.text]
            if child_texts:
                text_parts.append(f"[Contains: {'; '.join(child_texts)}...]")

        formatted_text = " ".join(text_parts)

        # Metadata
        metadata = {
            'section_num': section.section_num,
            'year': section.year,
            'provision_level': 'subsection',
            'provision_num': subsection.num,
            'heading': subsection.heading,
            'has_references': len(subsection.refs) > 0,
            'reference_count': len(subsection.refs),
        }

        subsections.append((subsection.id, formatted_text, metadata))

    return subsections


def embed_batch(texts: List[str], client: OpenAI, model: str = "text-embedding-3-small", max_retries: int = 3) -> List[List[float]]:
    """
    Embed a batch of texts using OpenAI API with retry logic.

    Args:
        texts: List of texts to embed
        client: OpenAI client
        model: Embedding model (default: text-embedding-3-small, 1536 dims)
        max_retries: Maximum number of retry attempts

    Returns:
        List of embedding vectors
    """
    if not client:
        raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY in .env")

    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model=model,
                input=texts,
                timeout=60.0  # 60 second timeout
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"  ⚠️  Retry {attempt + 1}/{max_retries} after {wait_time}s (Error: {str(e)[:50]}...)")
                time.sleep(wait_time)
            else:
                raise


def save_embeddings_to_json(
    embeddings_data: List[Dict],
    output_dir: Path = None
) -> None:
    """
    Save embeddings to JSON files organized by section/year.

    Args:
        embeddings_data: List of embedding dicts with metadata
        output_dir: Output directory (defaults to data/gold/embeddings)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / 'data' / 'gold' / 'embeddings'

    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by section and year
    by_section_year = {}
    for item in embeddings_data:
        # Extract from nested metadata structure
        if 'metadata' in item:
            section = item['metadata']['section_num']
            year = item['metadata']['year']
        else:
            # Flat structure (already has section_num at top level)
            section = item['section_num']
            year = item['year']

        key = f"{section}_{year}"

        if key not in by_section_year:
            by_section_year[key] = []

        by_section_year[key].append(item)

    # Save each section/year to separate file
    total_saved = 0
    for key, items in sorted(by_section_year.items()):
        output_file = output_dir / f"{key}.json"

        with open(output_file, 'w') as f:
            json.dump(items, f, indent=2)

        print(f"💾 Saved {len(items)} embeddings to {output_file.name}")
        total_saved += len(items)

    print(f"\n✅ Saved {total_saved} total embeddings to {output_dir}\n")


def embed_provisions_from_silver(
    sections_dir: Path = None,
    batch_size: int = 100,
    rate_limit_delay: float = 1.0,
    all_levels: bool = True,
    section_filter: str = None
) -> List[Dict]:
    """
    Extract and embed provisions from Silver JSONs.

    Args:
        sections_dir: Directory containing section JSONs
        batch_size: Number of texts to embed per API call
        rate_limit_delay: Delay between batches (seconds)
        all_levels: If True, extract all levels; if False, only subsections
        section_filter: Optional section number to process (e.g., "922")

    Returns:
        List of dicts with provision_id, text, embedding, metadata
    """
    if sections_dir is None:
        sections_dir = SILVER_SECTIONS_DIR

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Check .env file")

    client = OpenAI(api_key=OPENAI_API_KEY) if OpenAI else None

    level_desc = "all levels" if all_levels else "subsections only"
    print(f"\n🔍 Extracting {level_desc} from {sections_dir}\n")

    all_provisions = []
    section_dirs = sorted([d for d in sections_dir.iterdir() if d.is_dir()])

    # Filter sections if specified
    if section_filter:
        section_dirs = [d for d in section_dirs if d.name == section_filter]
        if not section_dirs:
            print(f"❌ Section {section_filter} not found")
            return []
        print(f"📍 Filtering to section: {section_filter}\n")

    # Extract all provisions first
    for section_dir in section_dirs:
        section_num = section_dir.name
        print(f"📄 Section {section_num}:")

        json_files = sorted(section_dir.glob('*.json'))
        for json_file in json_files:
            year = int(json_file.stem)

            with open(json_file, 'r') as f:
                data = json.load(f)

            section = SectionVersion(**data)

            # Choose extraction method based on all_levels flag
            if all_levels:
                provisions = flatten_all_provisions(section)
            else:
                provisions = extract_subsections(section)

            print(f"  {year}: {len(provisions)} provisions")
            all_provisions.extend(provisions)

    total = len(all_provisions)
    print(f"\n✅ Total provisions: {total}")
    print(f"📦 Batching into {(total + batch_size - 1) // batch_size} batches of {batch_size}\n")

    # Embed in batches
    embeddings_data = []

    for i in range(0, total, batch_size):
        batch = all_provisions[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"⚡ Embedding batch {batch_num}/{total_batches} ({len(batch)} provisions)...")

        texts = [text for _, text, _ in batch]

        try:
            embeddings = embed_batch(texts, client)

            for (prov_id, text, metadata), embedding in zip(batch, embeddings):
                embeddings_data.append({
                    'provision_id': prov_id,
                    'text_content': text,
                    'embedding': embedding,
                    'metadata': metadata
                })

            print(f"  ✅ Embedded {len(embeddings)} provisions")

            if i + batch_size < total:
                time.sleep(rate_limit_delay)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            raise

    print(f"\n{'='*60}")
    print(f"✅ Embedded {len(embeddings_data)} provisions")
    print(f"{'='*60}\n")

    return embeddings_data


if __name__ == "__main__":
    """Generate embeddings and save to JSON."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate embeddings for USC provisions')
    parser.add_argument('--section', type=str, help='Filter to specific section (e.g., 922)', default=None)
    parser.add_argument('--subsections-only', action='store_true', help='Extract only subsections (not all levels)')
    args = parser.parse_args()

    print("🚀 Starting embedding generation...\n")

    embeddings = embed_provisions_from_silver(
        all_levels=not args.subsections_only,
        section_filter=args.section
    )

    if embeddings:
        print(f"\n📊 Sample embedding (first 5 dims): {embeddings[0]['embedding'][:5]}")
        print(f"📏 Embedding dimension: {len(embeddings[0]['embedding'])}")

        # Save to JSON
        print(f"\n💾 Saving embeddings to JSON files...")
        save_embeddings_to_json(embeddings)

        print(f"✅ Complete! Run 'python pipeline/gold/load_embeddings_from_json.py' to load to PostgreSQL")
