#!/usr/bin/env python3
"""Debug script to inspect parsed IDs from 2018 and 2024 section 922."""

from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))

from services.data_loader import SectionDataLoader

# Initialize loader
loader = SectionDataLoader(Path('/Users/sergeyhlghatyan/dev/ocean/lelivre/app/data'))

# Parse 2018 section 922
print("=" * 80)
print("2018 Section 922 IDs")
print("=" * 80)

data_2018 = loader.get_section('922', 2018)

def print_ids(node, indent=0):
    """Recursively print all IDs in the tree."""
    prefix = "  " * indent
    node_id = node.get('id', 'NO ID')
    num = node.get('num', '')
    text_preview = node.get('text', '')[:60] + '...' if len(node.get('text', '')) > 60 else node.get('text', '')

    print(f"{prefix}{node_id} | {num} | {text_preview}")

    for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        for child in node.get(child_type, []):
            print_ids(child, indent + 1)

if data_2018:
    print_ids(data_2018)
else:
    print("Failed to parse 2018 section 922")

print("\n" + "=" * 80)
print("2024 Section 922 IDs (sample)")
print("=" * 80)

data_2024 = loader.get_section('922', 2024)

if data_2024:
    # Just print subsection (g) to compare
    for subsection in data_2024.get('subsections', []):
        if subsection.get('num') == '(g)':
            print_ids(subsection)
            break
else:
    print("Failed to parse 2024 section 922")

# Now let's specifically look for provision (ii) about "by its terms explicitly prohibits"
print("\n" + "=" * 80)
print("Searching for provisions containing 'by its terms explicitly prohibits'")
print("=" * 80)

def find_provisions(node, path=""):
    """Find all provisions containing the target text."""
    results = []

    node_id = node.get('id', 'NO ID')
    num = node.get('num', '')
    text = node.get('text', '')

    if 'by its terms explicitly prohibits' in text.lower():
        results.append({
            'id': node_id,
            'num': num,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'path': path
        })

    for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        for child in node.get(child_type, []):
            results.extend(find_provisions(child, path + f"/{child_type[:-1]}"))

    return results

if data_2018:
    results_2018 = find_provisions(data_2018)
    print(f"\n2018: Found {len(results_2018)} matching provisions")
    for r in results_2018:
        print(f"  ID: {r['id']}")
        print(f"  Num: {r['num']}")
        print(f"  Text: {r['text']}")
        print()

if data_2024:
    results_2024 = find_provisions(data_2024)
    print(f"2024: Found {len(results_2024)} matching provisions")
    for r in results_2024:
        print(f"  ID: {r['id']}")
        print(f"  Num: {r['num']}")
        print(f"  Text: {r['text']}")
        print()
