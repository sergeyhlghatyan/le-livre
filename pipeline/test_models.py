"""
Quick test script to validate Pydantic models against existing JSON data.
"""

import json
from pathlib import Path
from models.silver import SectionVersion

def test_section_validation():
    """Test that existing JSON validates against our Pydantic models."""

    # Load existing section JSON
    json_path = Path("../data/sections/922/2024.json")

    print(f"Loading {json_path}...")
    with open(json_path) as f:
        data = json.load(f)

    # Add required metadata fields that don't exist in old JSONs
    data['section_num'] = '922'
    data['year'] = 2024
    data['source_file'] = 'data/raw/uslm/2024/usc18.xml'
    data['source_format'] = 'xml'

    print("Validating with Pydantic...")
    try:
        section = SectionVersion(**data)

        # Print quality metrics
        print(f"\n✅ Validation successful!")
        print(f"\nSection: {section.section_num} - {section.heading}")
        print(f"Year: {section.year}")
        print(f"Provision count: {section.provision_count}")
        print(f"Reference count: {section.reference_count}")
        print(f"Max depth: {section.max_depth}")
        print(f"Subsections: {len(section.subsections)}")

        # Show a few references
        if section.reference_count > 0:
            print(f"\nFirst few references:")
            all_refs = []
            for subsection in section.subsections:
                all_refs.extend(subsection.get_all_references())

            for i, ref in enumerate(all_refs[:5]):
                print(f"  {i+1}. {ref.text} -> {ref.target}")

        return section

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        raise


if __name__ == "__main__":
    section = test_section_validation()
    print("\n✅ All tests passed!")
