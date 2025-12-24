#!/usr/bin/env python3
"""Quick test to check parsed structure of 2006 section 922."""

from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))

from services.usc_parser import parse_xhtml_section

# Parse 2006 section 922
xhtml_file = Path('/Users/sergeyhlghatyan/dev/ocean/lelivre/app/data/raw/uslm/2006/2006/2006usc18.htm')
data = parse_xhtml_section(xhtml_file, '922', 2006)

if not data:
    print("Failed to parse section")
    sys.exit(1)

# Find subsection (p)
def find_subsection_p(subsections):
    for sub in subsections:
        if sub.get('num') == '(p)':
            return sub
    return None

subsection_p = find_subsection_p(data.get('subsections', []))

if subsection_p:
    print("Subsection (p) structure:")
    print(f"  num: {subsection_p.get('num')}")
    print(f"  text: {subsection_p.get('text', '')[:100]}...")
    print(f"  paragraphs: {len(subsection_p.get('paragraphs', []))}")

    for i, para in enumerate(subsection_p.get('paragraphs', [])[:5]):
        print(f"\n  Paragraph {i}:")
        print(f"    num: {para.get('num')}")
        print(f"    text: {para.get('text', '')[:80]}...")
        print(f"    subparagraphs: {len(para.get('subparagraphs', []))}")

        for j, subpara in enumerate(para.get('subparagraphs', [])[:3]):
            print(f"      Subparagraph {j}: {subpara.get('num')} - {subpara.get('text', '')[:60]}...")
else:
    print("Subsection (p) not found")
    print(f"\nAvailable subsections: {[s.get('num') for s in data.get('subsections', [])]}")
