#!/usr/bin/env python3
"""
Hierarchical diff tool for comparing USC sections across years.
Preserves full hierarchy: subsection → paragraph → subparagraph → clause → subclause

Usage:
    python diff_paragraphs.py 922 2022 2024
    python diff_paragraphs.py 933 2022 2024
"""

import json
import re
import argparse
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup


# Hierarchy level mappings (from docs/usc-hierarchy.md)
TAG_TO_LEVEL = {
    'subsection': 5,
    'paragraph': 6,
    'subparagraph': 7,
    'clause': 8,
    'subclause': 9,
}

CLASS_TO_LEVEL = {
    'statutory-body': 5,      # Subsection
    'statutory-body-1em': 6,  # Paragraph
    'statutory-body-2em': 7,  # Subparagraph
    'statutory-body-3em': 8,  # Clause
    'statutory-body-4em': 9,  # Subclause
}


def extract_key_from_id(identifier: str) -> str:
    """Extract key from XML identifier.

    Example: /us/usc/t18/s922/a/1/A → a
             /us/usc/t18/s922/a/1/A/i → i
    """
    parts = identifier.split('/')
    # Find section (starts with 's'), return the part after it
    try:
        section_idx = next(i for i, p in enumerate(parts) if p.startswith('s'))
        if section_idx + 1 < len(parts):
            return parts[-1]  # Return last part (the specific key at this level)
    except (StopIteration, IndexError):
        pass
    return ''


def build_xml_tree(data: dict) -> dict:
    """Build hierarchical tree from XML section data."""
    tree = {}

    # Process subsections
    for subsection in data.get('subsections', []):
        key = extract_key_from_id(subsection['id'])
        tree[key] = {
            'num': subsection.get('num', ''),
            'text': subsection.get('text', '').strip(),
            'level': 5,
            'refs': subsection.get('refs', []),
            'children': _build_xml_children(subsection)
        }

    return tree


def _build_xml_children(node: dict) -> dict:
    """Recursively build children for XML nodes."""
    children = {}

    # Process each child type in order
    for child_type in ['paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        for child in node.get(child_type, []):
            key = extract_key_from_id(child['id'])
            tag = child.get('tag', child_type[:-1])  # Remove 's' from plural

            children[key] = {
                'num': child.get('num', ''),
                'text': child.get('text', '').strip(),
                'level': TAG_TO_LEVEL.get(tag, 5),
                'refs': child.get('refs', []),
                'children': _build_xml_children(child)  # Recurse
            }

    return children


def build_xhtml_tree(html: str) -> dict:
    """Build hierarchical tree from XHTML by parsing CSS classes."""
    soup = BeautifulSoup(html, 'html.parser')
    tree = {}

    # Stack to track current position: [(node_dict, level), ...]
    stack = [(tree, 4)]  # Start with root at section level (4)

    for p in soup.find_all('p', class_=re.compile(r'statutory-body')):
        # Get level from CSS class
        level = _get_level_from_class(p.get('class', []))

        # Extract numbering from text
        text = p.get_text().strip()
        match = re.match(r'^\(([a-zA-Z0-9]+)\)\s', text)

        if not match:
            continue  # Skip non-numbered elements (blocks, etc.)

        key = match.group(1).lower()

        # Pop stack until we find the correct parent level
        while stack and stack[-1][1] >= level:
            stack.pop()

        if not stack:
            # Shouldn't happen, but fallback to root
            stack = [(tree, 4)]

        # Get parent node
        parent_node, parent_level = stack[-1]

        # Create new node
        node = {
            'num': f'({match.group(1)})',
            'text': text,
            'level': level,
            'refs': [],  # Could extract <a> tags if needed
            'children': {}
        }

        # Add to parent
        parent_node[key] = node

        # Push to stack for potential children
        stack.append((node['children'], level))

    return tree


def _get_level_from_class(classes: list) -> int:
    """Map CSS class to hierarchy level."""
    for cls in classes:
        if cls in CLASS_TO_LEVEL:
            return CLASS_TO_LEVEL[cls]
    return 5  # Default to subsection


def diff_trees(old_tree: dict, new_tree: dict, path: str = '') -> List[Tuple]:
    """Recursively diff two hierarchical trees.

    Returns list of (status, path, level, old_node, new_node) tuples.
    Status: 'added', 'deleted', 'modified', 'unchanged'
    """
    results = []

    all_keys = sorted(set(old_tree.keys()) | set(new_tree.keys()))

    for key in all_keys:
        current_path = f'{path}/{key}' if path else key
        old_node = old_tree.get(key)
        new_node = new_tree.get(key)

        if old_node is None:
            # Added node
            level = new_node['level']
            results.append(('added', current_path, level, None, new_node))
            # Add all descendants as added
            results.extend(_get_all_descendants(new_node, current_path, 'added'))

        elif new_node is None:
            # Deleted node
            level = old_node['level']
            results.append(('deleted', current_path, level, old_node, None))
            # Add all descendants as deleted
            results.extend(_get_all_descendants(old_node, current_path, 'deleted'))

        else:
            # Node exists in both - check if modified
            level = old_node['level']
            old_text = old_node['text'].strip()
            new_text = new_node['text'].strip()

            if old_text != new_text:
                results.append(('modified', current_path, level, old_node, new_node))
            else:
                results.append(('unchanged', current_path, level, old_node, new_node))

            # Recursively diff children
            results.extend(diff_trees(
                old_node.get('children', {}),
                new_node.get('children', {}),
                current_path
            ))

    return results


def _get_all_descendants(node: dict, path: str, status: str) -> List[Tuple]:
    """Get all descendant nodes as diff results."""
    results = []
    for key, child in node.get('children', {}).items():
        child_path = f'{path}/{key}'
        level = child['level']

        if status == 'added':
            results.append((status, child_path, level, None, child))
        else:  # deleted
            results.append((status, child_path, level, child, None))

        # Recurse for grandchildren
        results.extend(_get_all_descendants(child, child_path, status))

    return results


def format_path(path: str) -> str:
    """Format path for display.

    Example: a/1/A → (a)(1)(A)
    """
    parts = path.split('/')
    return ''.join(f'({p})' for p in parts)


def word_diff_html(old_text: str, new_text: str) -> Tuple[str, str]:
    """Generate word-level diff with HTML highlighting."""
    old_words = old_text.split()
    new_words = new_text.split()

    differ = difflib.SequenceMatcher(None, old_words, new_words)

    old_html = []
    new_html = []

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            old_html.append(' '.join(old_words[i1:i2]))
            new_html.append(' '.join(new_words[j1:j2]))
        elif tag == 'delete':
            old_html.append(f'<span class="diff-remove">{" ".join(old_words[i1:i2])}</span>')
        elif tag == 'insert':
            new_html.append(f'<span class="diff-add">{" ".join(new_words[j1:j2])}</span>')
        elif tag == 'replace':
            old_html.append(f'<span class="diff-remove">{" ".join(old_words[i1:i2])}</span>')
            new_html.append(f'<span class="diff-add">{" ".join(new_words[j1:j2])}</span>')

    return ' '.join(old_html), ' '.join(new_html)


def generate_html_report(section_num: str, year1: int, year2: int, diff_results: List[Tuple]) -> str:
    """Generate HTML report with hierarchical indentation."""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>18 U.S.C. §{section_num} - {year1} vs {year2} (Hierarchical)</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 1600px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .stat {{
            padding: 10px 15px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .stat-added {{ background: #d4edda; color: #155724; }}
        .stat-deleted {{ background: #f8d7da; color: #721c24; }}
        .stat-modified {{ background: #fff3cd; color: #856404; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        th {{
            background: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 14px;
        }}
        td {{
            padding: 12px;
            border: 1px solid #dee2e6;
            vertical-align: top;
            font-size: 13px;
            line-height: 1.6;
        }}

        /* Hierarchy indentation */
        .indent-0 {{ padding-left: 10px; }}    /* Subsection */
        .indent-1 {{ padding-left: 30px; }}    /* Paragraph */
        .indent-2 {{ padding-left: 50px; }}    /* Subparagraph */
        .indent-3 {{ padding-left: 70px; }}    /* Clause */
        .indent-4 {{ padding-left: 90px; }}    /* Subclause */

        /* Level styling */
        .level-5 {{ font-weight: bold; }}      /* Subsection - bold */
        .level-6 {{ }}                          /* Paragraph - normal */
        .level-7 {{ font-style: italic; }}     /* Subparagraph - italic */
        .level-8 {{ font-size: 0.95em; }}      /* Clause - smaller */
        .level-9 {{ font-size: 0.9em; }}       /* Subclause - smallest */

        .para-num {{
            font-weight: bold;
            color: #007bff;
            width: 120px;
            font-family: monospace;
        }}

        /* Status colors */
        .added {{ background-color: #d4edda; }}
        .deleted {{ background-color: #f8d7da; }}
        .modified {{ background-color: #fff3cd; }}
        .unchanged {{ opacity: 0.5; }}

        /* Word-level diff */
        .diff-add {{
            background-color: #28a745;
            color: white;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .diff-remove {{
            background-color: #dc3545;
            color: white;
            padding: 2px 4px;
            border-radius: 3px;
            text-decoration: line-through;
        }}

        .empty-cell {{
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>18 U.S.C. §{section_num} Hierarchical Comparison</h1>
    <div class="summary">
        <h2>Comparing {year1} → {year2}</h2>
        <div class="summary-stats">
"""

    # Calculate statistics
    stats = {'added': 0, 'deleted': 0, 'modified': 0, 'unchanged': 0}
    for status, _, _, _, _ in diff_results:
        stats[status] += 1

    html += f"""
            <div class="stat stat-added">Added: {stats['added']}</div>
            <div class="stat stat-deleted">Deleted: {stats['deleted']}</div>
            <div class="stat stat-modified">Modified: {stats['modified']}</div>
            <div class="stat">Unchanged: {stats['unchanged']}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Provision</th>
                <th>{year1}</th>
                <th>{year2}</th>
            </tr>
        </thead>
        <tbody>
"""

    # Generate rows with hierarchy
    for status, path, level, old_node, new_node in diff_results:
        indent_level = level - 5  # Subsection=0, paragraph=1, etc.
        indent_class = f'indent-{indent_level}'
        level_class = f'level-{level}'
        display_path = format_path(path)

        if status == 'added':
            html += f"""
            <tr class="added {level_class}">
                <td class="para-num {indent_class}">{display_path}</td>
                <td class="empty-cell">—</td>
                <td>{new_node['text']}</td>
            </tr>
"""
        elif status == 'deleted':
            html += f"""
            <tr class="deleted {level_class}">
                <td class="para-num {indent_class}">{display_path}</td>
                <td>{old_node['text']}</td>
                <td class="empty-cell">—</td>
            </tr>
"""
        elif status == 'modified':
            old_html, new_html = word_diff_html(old_node['text'], new_node['text'])
            html += f"""
            <tr class="modified {level_class}">
                <td class="para-num {indent_class}">{display_path}</td>
                <td>{old_html}</td>
                <td>{new_html}</td>
            </tr>
"""
        else:  # unchanged
            html += f"""
            <tr class="unchanged {level_class}">
                <td class="para-num {indent_class}">{display_path}</td>
                <td>{old_node['text']}</td>
                <td>{new_node['text']}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>
</body>
</html>
"""

    return html


def load_section_tree(section_file: Path) -> dict:
    """Load section JSON and build hierarchical tree."""
    with open(section_file, 'r') as f:
        data = json.load(f)

    # Check format
    if data.get('metadata', {}).get('format') == 'xml':
        return build_xml_tree(data)
    else:
        # XHTML format
        return build_xhtml_tree(data.get('raw_html', ''))


def main():
    parser = argparse.ArgumentParser(
        description='Generate hierarchical diff of USC sections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python diff_paragraphs.py 922 2022 2024
  python diff_paragraphs.py 933 2022 2024
  python diff_paragraphs.py 922 1994 2024
"""
    )

    parser.add_argument('section', type=str, help='Section number (e.g., 922, 933)')
    parser.add_argument('year1', type=int, help='First year (older version)')
    parser.add_argument('year2', type=int, help='Second year (newer version)')
    parser.add_argument('--output', '-o', type=Path, help='Output HTML file (default: data/diffs/)')

    args = parser.parse_args()

    # Load section files
    base_dir = Path('data/sections')
    section_dir = base_dir / args.section

    file1 = section_dir / f'{args.year1}.json'
    file2 = section_dir / f'{args.year2}.json'

    if not file1.exists():
        print(f"✗ File not found: {file1}")
        return 1

    if not file2.exists():
        print(f"✗ File not found: {file2}")
        return 1

    print(f"\n{'='*60}")
    print(f"Hierarchical Diff: §{args.section} ({args.year1} vs {args.year2})")
    print(f"{'='*60}\n")

    # Load and build trees
    print(f"Building tree from {file1.name}...")
    old_tree = load_section_tree(file1)
    old_count = _count_nodes(old_tree)
    print(f"  → {old_count} nodes in hierarchy")

    print(f"Building tree from {file2.name}...")
    new_tree = load_section_tree(file2)
    new_count = _count_nodes(new_tree)
    print(f"  → {new_count} nodes in hierarchy")

    # Compute diff
    print("\nComputing hierarchical diff...")
    diff_results = diff_trees(old_tree, new_tree)

    # Statistics
    stats = {'added': 0, 'deleted': 0, 'modified': 0, 'unchanged': 0}
    for status, _, _, _, _ in diff_results:
        stats[status] += 1

    print(f"  ✓ Added: {stats['added']}")
    print(f"  ✓ Deleted: {stats['deleted']}")
    print(f"  ✓ Modified: {stats['modified']}")
    print(f"  ✓ Unchanged: {stats['unchanged']}")

    # Generate HTML
    print("\nGenerating HTML report...")
    html = generate_html_report(args.section, args.year1, args.year2, diff_results)

    # Write output
    if args.output:
        output_file = args.output
    else:
        output_dir = Path('data/diffs')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'{args.section}_{args.year1}_vs_{args.year2}.html'

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"  ✓ Saved to: {output_file}")
    print(f"\n{'='*60}\n")

    return 0


def _count_nodes(tree: dict) -> int:
    """Count total nodes in tree."""
    count = len(tree)
    for node in tree.values():
        count += _count_nodes(node.get('children', {}))
    return count


if __name__ == '__main__':
    exit(main())
