"""
Silver stage parser: Wrap existing USC parser with Pydantic validation.

This module imports the existing parser from app/services/usc_parser.py
(without modifying it) and adds validation + quality gates.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

# Add parent directory to path to import from app/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.usc_parser import parse_xml_section, parse_xhtml_section
from pipeline.models.silver import SectionVersion


# Configuration for year sources
YEAR_CONFIG = {
    1994: {'file': 'data/raw/uslm/1994/1994/1994usc18.htm', 'format': 'xhtml'},
    2000: {'file': 'data/raw/uslm/2000/2000/2000usc18.htm', 'format': 'xhtml'},
    2006: {'file': 'data/raw/uslm/2006/2006/2006usc18.htm', 'format': 'xhtml'},
    2013: {'file': 'data/raw/uslm/2013/2013/2013usc18.htm', 'format': 'xhtml'},
    2018: {'file': 'data/raw/uslm/2018/2018/2018usc18.htm', 'format': 'xhtml'},
    2022: {'file': 'data/raw/uslm/2022/usc18.xml', 'format': 'xml'},
    2024: {'file': 'data/raw/uslm/2024/usc18.xml', 'format': 'xml'},
}


def parse_section_to_silver(
    section_num: str,
    year: int,
    base_dir: Path = None
) -> Optional[SectionVersion]:
    """
    Parse a single section and validate with Pydantic.

    Args:
        section_num: Section number (e.g., "922", "933")
        year: Year to parse (1994-2024)
        base_dir: Base directory (defaults to project root)

    Returns:
        Validated SectionVersion or None if parsing fails

    Raises:
        ValueError: If year not supported
        ValidationError: If parsed data doesn't match schema
    """
    if year not in YEAR_CONFIG:
        raise ValueError(f"Year {year} not supported. Available: {list(YEAR_CONFIG.keys())}")

    # Get source file config
    config = YEAR_CONFIG[year]
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent
    source_file = base_dir / config['file']

    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # Parse using existing parser
    print(f"  Parsing § {section_num} ({year}) from {source_file.name}...")

    try:
        if config['format'] == 'xml':
            data = parse_xml_section(source_file, section_num, year)
        else:
            data = parse_xhtml_section(source_file, section_num, year)

        if not data:
            print(f"  ⚠️  Section {section_num} not found in {year}")
            return None

        # Add required metadata fields for Pydantic validation
        data['section_num'] = section_num
        data['year'] = year
        data['source_file'] = str(source_file.relative_to(base_dir))
        data['source_format'] = config['format']
        data['parsed_at'] = datetime.now()
        data['parser_version'] = "1.0"

        # Remove old metadata if present
        if 'metadata' in data:
            del data['metadata']

        # Validate with Pydantic
        section = SectionVersion(**data)

        print(f"  ✅ Validated: {section.provision_count} provisions, "
              f"{section.reference_count} refs, max depth {section.max_depth}")

        return section

    except Exception as e:
        print(f"  ❌ Error parsing § {section_num} ({year}): {e}")
        raise


def save_section_to_silver(section: SectionVersion, base_dir: Path = None) -> Path:
    """
    Save validated section to Silver storage.

    Args:
        section: Validated SectionVersion
        base_dir: Base directory (defaults to project root)

    Returns:
        Path where section was saved
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent

    # Create directory structure: data/silver/sections/{section_num}/
    output_dir = base_dir / 'data' / 'silver' / 'sections' / section.section_num
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to {year}.json
    output_file = output_dir / f'{section.year}.json'

    print(f"  💾 Saving to {output_file.relative_to(base_dir)}")

    # Convert to dict and save as JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        # Use model_dump() for Pydantic v2, exclude computed fields from serialization
        json.dump(
            section.model_dump(mode='json', exclude={'provision_count', 'reference_count', 'max_depth'}),
            f,
            indent=2,
            ensure_ascii=False
        )

    return output_file


def parse_all_sections(
    section_nums: List[str],
    years: List[int],
    base_dir: Path = None
) -> Tuple[List[SectionVersion], List[str]]:
    """
    Parse multiple sections across multiple years.

    Args:
        section_nums: List of section numbers (e.g., ["922", "933"])
        years: List of years to parse (e.g., [1994, 2000, 2024])
        base_dir: Base directory (defaults to project root)

    Returns:
        Tuple of (successfully parsed sections, list of errors)
    """
    sections = []
    errors = []

    total = len(section_nums) * len(years)
    print(f"\n🔄 Parsing {len(section_nums)} sections × {len(years)} years = {total} section-years\n")

    for section_num in section_nums:
        print(f"📄 Section {section_num}:")
        for year in years:
            try:
                section = parse_section_to_silver(section_num, year, base_dir)
                if section:
                    save_section_to_silver(section, base_dir)
                    sections.append(section)
                else:
                    error_msg = f"{section_num}:{year} - Section not found"
                    errors.append(error_msg)

            except Exception as e:
                error_msg = f"{section_num}:{year} - {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        print()  # Blank line between sections

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Successfully parsed: {len(sections)}/{total}")
    if errors:
        print(f"❌ Errors: {len(errors)}")
        print("\nError details:")
        for error in errors:
            print(f"  - {error}")
    print(f"{'='*60}\n")

    return sections, errors


if __name__ == "__main__":
    """Test the parser with sections 922 and 933."""

    # Test sections
    section_nums = ["922", "933"]
    years = [1994, 2000, 2006, 2013, 2018, 2022, 2024]

    sections, errors = parse_all_sections(section_nums, years)

    if not errors:
        print("🎉 All sections parsed successfully!")
    else:
        print(f"⚠️  Completed with {len(errors)} errors")
