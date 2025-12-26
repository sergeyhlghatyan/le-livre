"""
Reference extractor: Flatten hierarchical references to JSONL for graph DB ingestion.

This module reads Silver JSONs and extracts all cross-references into a flat
structure suitable for loading into Neo4j.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.models.silver import SectionVersion, ReferenceRecord, Provision, Reference


def parse_usc_path(href: str) -> Dict[str, any]:
    """
    Parse a USC reference path to extract title and section numbers.

    Args:
        href: Reference path (e.g., '/us/usc/t18/s923', '/us/usc/t21/s802')

    Returns:
        Dict with parsed components: {
            'title': int,
            'section': str,
            'provision_id': str (full path)
        }
    """
    # Handle HTML anchors
    if href.startswith('#'):
        return {
            'title': None,
            'section': None,
            'provision_id': href,
            'is_internal_anchor': True
        }

    # Handle Public Law and Statutes
    if href.startswith('/us/pl/') or href.startswith('/us/stat/'):
        return {
            'title': None,
            'section': None,
            'provision_id': href,
            'is_external': True
        }

    # Parse USC path: /us/usc/t18/s922/a/1
    match = re.match(r'/us/usc/t(\d+)/s(\d+[a-z]?)(.*)', href)
    if match:
        title = int(match.group(1))
        section = match.group(2)
        remainder = match.group(3)  # e.g., /a/1

        return {
            'title': title,
            'section': section,
            'provision_id': href,
            'is_usc': True
        }

    # Fallback
    return {
        'title': None,
        'section': None,
        'provision_id': href,
        'is_unknown': True
    }


def extract_references_from_section(
    section: SectionVersion
) -> List[ReferenceRecord]:
    """
    Extract all references from a section into flat ReferenceRecord list.

    Args:
        section: Validated SectionVersion

    Returns:
        List of ReferenceRecord objects
    """
    records = []
    ref_id = 0

    def extract_from_provision(prov: Provision, source_section_num: str):
        """Recursively extract references from provision tree."""
        nonlocal ref_id

        for ref in prov.refs:
            # Parse target
            parsed = parse_usc_path(ref.target)

            # Determine reference type
            if parsed.get('is_usc'):
                if parsed['title'] == 18:
                    ref_type = 'internal'
                else:
                    ref_type = 'cross_title'
            else:
                # HTML anchors, Public Laws, etc. - treat as internal for now
                ref_type = 'internal'

            # Create ReferenceRecord
            record = ReferenceRecord(
                id=f"{source_section_num}:{section.year}:ref{ref_id}",
                year=section.year,
                source_section=source_section_num,
                source_provision_id=prov.id,
                target_section=parsed.get('section'),
                target_provision_id=ref.target,
                target_title=parsed.get('title'),
                display_text=ref.text,
                ref_type=ref_type
            )

            records.append(record)
            ref_id += 1

        # Recurse to children
        for child_list in [
            prov.subsections,
            prov.paragraphs,
            prov.subparagraphs,
            prov.clauses,
            prov.subclauses
        ]:
            for child in child_list:
                extract_from_provision(child, source_section_num)

    # Extract from all subsections
    for subsection in section.subsections:
        extract_from_provision(subsection, section.section_num)

    return records


def extract_references_from_directory(
    sections_dir: Path,
    output_dir: Path
) -> Dict[int, int]:
    """
    Extract references from all Silver JSON files organized by year.

    Args:
        sections_dir: Directory containing section subdirectories
        output_dir: Directory to write JSONL files (data/silver/references/)

    Returns:
        Dict mapping year -> reference count
    """
    print(f"\n🔍 Extracting references from {sections_dir}\n")

    # Group files by year
    year_refs = {}  # year -> List[ReferenceRecord]

    # Find all section directories
    section_dirs = sorted([d for d in sections_dir.iterdir() if d.is_dir()])

    for section_dir in section_dirs:
        section_num = section_dir.name
        print(f"📄 Section {section_num}:")

        # Find all year JSONs in this section
        json_files = sorted(section_dir.glob('*.json'))

        for json_file in json_files:
            year = int(json_file.stem)  # e.g., 2024.json -> 2024

            try:
                # Load and parse
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                section = SectionVersion(**data)

                # Extract references
                refs = extract_references_from_section(section)

                if refs:
                    print(f"  {year}: {len(refs)} references")

                    # Add to year collection
                    if year not in year_refs:
                        year_refs[year] = []
                    year_refs[year].extend(refs)
                else:
                    print(f"  {year}: No references")

            except Exception as e:
                print(f"  ❌ Error processing {json_file.name}: {e}")

    # Write JSONL files per year
    print(f"\n💾 Writing JSONL files to {output_dir}\n")
    output_dir.mkdir(parents=True, exist_ok=True)

    year_counts = {}
    for year in sorted(year_refs.keys()):
        refs = year_refs[year]
        output_file = output_dir / f'{year}.jsonl'

        with open(output_file, 'w', encoding='utf-8') as f:
            for ref in refs:
                # Write each reference as a JSON line
                f.write(ref.model_dump_json() + '\n')

        year_counts[year] = len(refs)
        print(f"  {year}.jsonl: {len(refs)} references")

    print(f"\n{'='*60}")
    print(f"✅ Total references extracted: {sum(year_counts.values())}")
    print(f"✅ Years covered: {len(year_counts)}")
    print(f"{'='*60}\n")

    return year_counts


if __name__ == "__main__":
    """Extract references from Silver JSONs."""

    base_dir = Path(__file__).parent.parent.parent
    sections_dir = base_dir / 'data' / 'silver' / 'sections'
    output_dir = base_dir / 'data' / 'silver' / 'references'

    year_counts = extract_references_from_directory(sections_dir, output_dir)

    if year_counts:
        print("🎉 Reference extraction complete!")
    else:
        print("⚠️  No references found")
