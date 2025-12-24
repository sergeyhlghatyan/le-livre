#!/usr/bin/env python3
"""
Analyze historical changes to USC sections across all available years.
Generates HTML and CSV reports showing change frequency and timelines.
"""

import json
import csv
import sys
from pathlib import Path
from typing import Optional
from lxml import etree
from bs4 import BeautifulSoup
import re

# Hierarchy level mappings
TAG_TO_LEVEL = {
    'subsection': 5,
    'paragraph': 6,
    'subparagraph': 7,
    'clause': 8,
    'subclause': 9,
}

CLASS_TO_LEVEL = {
    'statutory-body': 5,
    'statutory-body-1em': 6,
    'statutory-body-2em': 7,
    'statutory-body-3em': 8,
    'statutory-body-4em': 9,
}

LEVEL_TO_NAME = {
    5: 'subsection',
    6: 'paragraph',
    7: 'subparagraph',
    8: 'clause',
    9: 'subclause',
}


# ============================================================================
# Tree Building Functions (from diff_paragraphs.py)
# ============================================================================

def extract_key_from_id(identifier: str) -> str:
    """Extract subdivision key from identifier."""
    parts = identifier.split('/')
    section_idx = next((i for i, p in enumerate(parts) if p.startswith('s')), -1)
    if section_idx == -1 or section_idx + 1 >= len(parts):
        return ''
    return parts[-1]


def build_xml_tree(data: dict) -> dict:
    """Build hierarchical tree from XML section data."""
    tree = {}
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
    for child_type in ['paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        for child in node.get(child_type, []):
            key = extract_key_from_id(child['id'])
            tag = child.get('tag', child_type[:-1])
            children[key] = {
                'num': child.get('num', ''),
                'text': child.get('text', '').strip(),
                'level': TAG_TO_LEVEL.get(tag, 5),
                'refs': child.get('refs', []),
                'children': _build_xml_children(child)
            }
    return children


def _get_level_from_class(classes: list) -> int:
    """Get hierarchy level from CSS class."""
    for cls in classes:
        if cls in CLASS_TO_LEVEL:
            return CLASS_TO_LEVEL[cls]
    return 5


def build_xhtml_tree(html: str) -> dict:
    """Build hierarchical tree from XHTML by parsing CSS classes."""
    soup = BeautifulSoup(html, 'html.parser')
    tree = {}
    stack = [(tree, 4)]  # Start with root at section level

    for p in soup.find_all('p', class_=re.compile(r'statutory-body')):
        level = _get_level_from_class(p.get('class', []))
        text = p.get_text().strip()
        match = re.match(r'^\(([a-zA-Z0-9]+)\)\s', text)

        if not match:
            continue

        key = match.group(1).lower()

        # Pop stack until we find correct parent level
        while stack and stack[-1][1] >= level:
            stack.pop()

        if not stack:
            stack = [(tree, 4)]

        parent_node, parent_level = stack[-1]

        node = {
            'num': f'({match.group(1)})',
            'text': text,
            'level': level,
            'refs': [],
            'children': {}
        }

        parent_node[key] = node
        stack.append((node['children'], level))

    return tree


def load_section_tree(json_file: Path) -> dict:
    """Load section JSON and build tree."""
    with open(json_file) as f:
        data = json.load(f)

    fmt = data.get('metadata', {}).get('format', 'xml')

    if fmt == 'xml':
        return build_xml_tree(data)
    else:
        html = data.get('raw_html', '')
        return build_xhtml_tree(html)


# ============================================================================
# Helper Functions for Path Navigation
# ============================================================================

def get_all_paths(tree: dict, prefix: str = '') -> list:
    """Get all provision paths in tree."""
    paths = []
    for key, node in tree.items():
        path = f'{prefix}/{key}' if prefix else key
        paths.append(path)
        if 'children' in node and node['children']:
            paths.extend(get_all_paths(node['children'], path))
    return paths


def get_node_at_path(tree: dict, path: str) -> Optional[dict]:
    """Get node at specific path in tree."""
    parts = path.split('/')
    current = tree

    for i, part in enumerate(parts):
        if part not in current:
            return None
        if i == len(parts) - 1:
            return current[part]
        current = current[part].get('children', {})

    return None


def get_level_from_path(path: str, tree: dict) -> int:
    """Get hierarchy level for a path."""
    node = get_node_at_path(tree, path)
    return node['level'] if node else 0


def format_path(path: str) -> str:
    """Format path for display: a/1/A -> (a)(1)(A)"""
    parts = path.split('/')
    return ''.join(f'({p})' for p in parts)


# ============================================================================
# Analysis Functions
# ============================================================================

def load_all_versions(section_num: str) -> dict:
    """Load all available versions and build trees.

    Returns: {year: tree_dict}
    """
    versions = {}
    section_dir = Path(f'data/sections/{section_num}')

    if not section_dir.exists():
        print(f"Error: Section directory not found: {section_dir}")
        return versions

    for json_file in sorted(section_dir.glob('*.json')):
        year = int(json_file.stem)
        tree = load_section_tree(json_file)
        versions[year] = tree
        print(f"  Loaded {year}: {len(get_all_paths(tree))} provisions")

    return versions


def track_provision_history(versions: dict) -> dict:
    """Track each provision across all years.

    Returns: {
        'a/1/A': {
            'level': 7,
            'history': {
                1994: {'status': 'exists', 'text': '...'},
                2000: {'status': 'modified', 'text': '...'},
            },
            'first_seen': 1994,
            'last_modified': 2000,
            'total_changes': 1,
            'status': 'active'
        }
    }
    """
    all_provisions = {}

    # Collect all unique provision paths
    for year, tree in sorted(versions.items()):
        for path in get_all_paths(tree):
            if path not in all_provisions:
                all_provisions[path] = {
                    'level': get_level_from_path(path, tree),
                    'history': {},
                    'first_seen': year,
                    'last_modified': None,
                    'total_changes': 0,
                    'status': 'active'
                }

    # Track status year by year
    years = sorted(versions.keys())
    for path, provision_data in all_provisions.items():
        prev_text = None

        for year in years:
            node = get_node_at_path(versions[year], path)

            if node is None:
                provision_data['history'][year] = {'status': 'missing', 'text': ''}
            else:
                text = node['text'].strip()

                if prev_text is None:
                    # First appearance
                    status = 'added' if year > provision_data['first_seen'] else 'exists'
                elif text != prev_text:
                    # Modified
                    status = 'modified'
                    provision_data['total_changes'] += 1
                    provision_data['last_modified'] = year
                else:
                    # Unchanged
                    status = 'unchanged'

                provision_data['history'][year] = {
                    'status': status,
                    'text': text
                }
                prev_text = text

        # Determine final status
        last_year = years[-1]
        if provision_data['history'][last_year]['status'] == 'missing':
            provision_data['status'] = 'deleted'
        elif provision_data['first_seen'] == last_year:
            provision_data['status'] = 'new'
        else:
            provision_data['status'] = 'active'

    return all_provisions


def calculate_statistics(provision_history: dict) -> dict:
    """Calculate summary statistics."""
    stats = {
        'total_provisions': len(provision_history),
        'most_changed': None,
        'most_stable': [],
        'new_provisions': [],
        'deleted_provisions': [],
        'change_distribution': {}
    }

    max_changes = 0
    for path, data in provision_history.items():
        changes = data['total_changes']

        # Track most changed
        if changes > max_changes:
            max_changes = changes
            stats['most_changed'] = (path, changes)

        # Track stable (0 changes)
        if changes == 0 and data['status'] == 'active':
            stats['most_stable'].append(path)

        # Track new/deleted
        if data['status'] == 'new':
            stats['new_provisions'].append(path)
        elif data['status'] == 'deleted':
            stats['deleted_provisions'].append(path)

        # Distribution
        stats['change_distribution'][changes] = \
            stats['change_distribution'].get(changes, 0) + 1

    return stats


# ============================================================================
# Report Generation
# ============================================================================

def find_all_refs(node: dict, refs_list: list):
    """Recursively find all references in a section tree."""
    if 'refs' in node:
        refs_list.extend(node['refs'])
    for key in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        if key in node:
            for child in node[key]:
                find_all_refs(child, refs_list)


def generate_reference_section(section_num: str) -> str:
    """Generate HTML section showing cross-references."""
    # Load latest version to get references
    latest_json = Path(f'data/sections/{section_num}/2024.json')
    if not latest_json.exists():
        return ''

    with open(latest_json) as f:
        data = json.load(f)

    refs = []
    find_all_refs(data, refs)

    if not refs:
        return ''

    # Group by target
    import re
    ref_groups = {}
    for ref in refs:
        target = ref['target']
        if target not in ref_groups:
            ref_groups[target] = {
                'texts': [],
                'title': None,
                'section': None,
                'type': 'external'
            }
        ref_groups[target]['texts'].append(ref['text'])

        # Parse target
        match = re.search(r'/t(\d+)/s(\d+)', target)
        if match:
            title, sec = match.groups()
            ref_groups[target]['title'] = title
            ref_groups[target]['section'] = sec
            if title == '18':
                # Check if we have this section
                if Path(f'data/sections/{sec}/2024.json').exists():
                    ref_groups[target]['type'] = 'internal'

    html = '<h2>Cross-References</h2>\n'
    html += f'<p>This section references {len(ref_groups)} other statute(s):</p>\n<ul class="ref-list">\n'

    for target, info in sorted(ref_groups.items(), key=lambda x: (x[1]['title'] or '', x[1]['section'] or '')):
        if info['type'] == 'internal':
            # Local reference with link to section view
            html += f'<li class="ref-item">'
            html += f'<a href="../views/{info["section"]}.html" class="statute-ref">'
            html += f'Title {info["title"]} § {info["section"]}'
            html += f'</a>'
            html += f' <span class="ref-count">({len(info["texts"])} reference{"s" if len(info["texts"]) > 1 else ""})</span>'
            html += f'</li>\n'
        elif info['title'] and info['section']:
            # External reference - link to uscode.house.gov
            external_url = f'https://uscode.house.gov/view.xhtml?req={target.replace("/", ":")}'
            html += f'<li class="ref-item">'
            html += f'<a href="{external_url}" class="external-ref" target="_blank">'
            html += f'Title {info["title"]} § {info["section"]}'
            html += f'</a>'
            html += f' <span class="ref-count">({len(info["texts"])} reference{"s" if len(info["texts"]) > 1 else ""})</span>'
            html += f'</li>\n'
        else:
            # Other reference (public law, etc.)
            html += f'<li class="ref-item other-ref">{target}'
            html += f' <span class="ref-count">({len(info["texts"])} reference{"s" if len(info["texts"]) > 1 else ""})</span>'
            html += f'</li>\n'

    html += '</ul>\n'
    return html


def generate_timeline(years: list, history: dict) -> str:
    """Generate ASCII timeline for a provision."""
    timeline_parts = []

    for i, year in enumerate(years):
        year_info = history.get(year, {})
        status = year_info.get('status', 'missing')

        if status == 'missing':
            continue
        elif status == 'modified':
            timeline_parts.append(f"{year}(M)")
        elif status == 'added':
            timeline_parts.append(f"[{year}]")
        else:
            timeline_parts.append(str(year))

    return '────'.join(timeline_parts)


def natural_sort_key(path: str) -> tuple:
    """Natural sort key for hierarchical paths.

    Converts 'a/1/A' to sortable tuple handling numbers properly.
    """
    def convert(part):
        # Try to convert to int for numeric parts
        if part.isdigit():
            return (0, int(part))
        # Roman numerals (i, ii, iii, I, II, III)
        elif part.lower() in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']:
            roman_values = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
                          'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10}
            return (1, roman_values.get(part.lower(), 0))
        # Letters
        else:
            return (2, part.lower())

    return tuple(convert(part) for part in path.split('/'))


def get_tree_prefix(path: str, all_paths: list) -> str:
    """Generate tree connector prefix for a provision."""
    parts = path.split('/')
    level = len(parts)

    if level == 1:
        return ''

    # Check if this is the last child of its parent
    parent = '/'.join(parts[:-1]) if len(parts) > 1 else ''
    siblings = [p for p in all_paths if (
        '/'.join(p.split('/')[:-1]) == parent and len(p.split('/')) == level
    )]
    is_last = path == sorted(siblings, key=natural_sort_key)[-1]

    # Build prefix with proper connectors
    prefix_parts = []
    for i in range(1, level):
        ancestor_parts = parts[:i]
        ancestor_path = '/'.join(ancestor_parts)
        ancestor_parent = '/'.join(ancestor_parts[:-1]) if len(ancestor_parts) > 1 else ''

        # Get siblings of this ancestor
        ancestor_siblings = [p for p in all_paths if (
            '/'.join(p.split('/')[:-1]) == ancestor_parent and
            len(p.split('/')) == len(ancestor_parts)
        )]

        # Check if ancestor is last among its siblings
        is_ancestor_last = ancestor_path == sorted(ancestor_siblings, key=natural_sort_key)[-1] if ancestor_siblings else True

        # Add vertical line if ancestor is not last (more siblings below)
        if not is_ancestor_last:
            prefix_parts.append('│   ')
        else:
            prefix_parts.append('    ')

    # Add final connector
    prefix_parts.append('└── ' if is_last else '├── ')

    return ''.join(prefix_parts)


def generate_html_report(section_num: str, provision_history: dict, stats: dict, years: list) -> str:
    """Generate HTML report with statistics and tables."""

    # Sort provisions hierarchically
    sorted_provisions = sorted(
        provision_history.items(),
        key=lambda x: natural_sort_key(x[0])
    )

    all_paths = [p for p, _ in sorted_provisions]

    # Generate table rows with hierarchy
    table_rows = []
    for path, data in sorted_provisions:
        status_class = data['status']
        level_name = LEVEL_TO_NAME.get(data['level'], 'unknown')
        timeline = generate_timeline(years, data['history'])
        level = data['level']

        # Tree visualization
        tree_prefix = get_tree_prefix(path, all_paths)

        # Change badge
        changes = data['total_changes']
        if changes == 0:
            change_badge = '<span class="badge badge-stable">0</span>'
        elif changes <= 2:
            change_badge = f'<span class="badge badge-low">{changes}</span>'
        else:
            change_badge = f'<span class="badge badge-high">{changes}</span>'

        # Format provision with tree structure
        provision_display = f'{tree_prefix}{format_path(path)} {change_badge}'

        table_rows.append(f"""
            <tr class="{status_class}">
                <td class="provision-cell">{provision_display}</td>
                <td>{level_name}</td>
                <td>{data['total_changes']}</td>
                <td>{data['first_seen']}</td>
                <td>{data['last_modified'] or '-'}</td>
                <td>{data['status']}</td>
                <td class="timeline">{timeline}</td>
            </tr>
        """)

    # Most changed provisions for visualization
    top_changed = sorted_provisions[:10]
    timeline_viz = []
    for path, data in top_changed:
        if data['total_changes'] == 0:
            continue
        formatted = format_path(path)
        timeline = generate_timeline(years, data['history'])
        timeline_viz.append(f"""
            <div style="margin-bottom: 15px;">
                <strong>{formatted}</strong> - {data['total_changes']} change(s)<br>
                <span class="timeline">{timeline}</span>
            </div>
        """)

    most_changed_str = f"{format_path(stats['most_changed'][0])} - {stats['most_changed'][1]} changes" if stats['most_changed'] else "None"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>§{section_num} Change Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #333;
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        ul {{
            background: #f9f9f9;
            padding: 20px 40px;
            border-left: 4px solid #0066cc;
        }}
        li {{
            margin: 8px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background: #0066cc;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .stable {{
            background: #d4edda;
        }}
        .active {{
            background: #fff3cd;
        }}
        .deleted {{
            background: #f8d7da;
        }}
        .new {{
            background: #cfe2ff;
        }}
        .timeline {{
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            white-space: nowrap;
            overflow-x: auto;
        }}
        .legend {{
            background: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .provision-cell {{
            font-family: 'Monaco', 'Courier New', monospace;
            white-space: pre;
            font-size: 13px;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
            color: white;
            margin-left: 8px;
        }}
        .badge-stable {{
            background: #28a745;
        }}
        .badge-low {{
            background: #ffc107;
            color: #333;
        }}
        .badge-high {{
            background: #dc3545;
        }}
        .statute-ref {{
            color: #0066cc;
            text-decoration: none;
            border-bottom: 1px dotted #0066cc;
            font-weight: 600;
        }}
        .statute-ref:hover {{
            background: #e3f2fd;
            border-bottom: 1px solid #0066cc;
        }}
        .external-ref {{
            color: #666;
            text-decoration: none;
            border-bottom: 1px dotted #666;
        }}
        .external-ref::after {{
            content: ' ↗';
            font-size: 0.8em;
        }}
        .external-ref:hover {{
            background: #f5f5f5;
        }}
        .ref-count {{
            color: #888;
            font-size: 0.9em;
            font-style: italic;
        }}
        .ref-list {{
            list-style: none;
            padding-left: 0;
        }}
        .ref-item {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .other-ref {{
            color: #666;
            font-family: monospace;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>18 U.S.C. §{section_num} - Historical Change Analysis</h1>

    <h2>Summary Statistics</h2>
    <ul>
        <li>Total provisions tracked: <strong>{stats['total_provisions']}</strong></li>
        <li>Most frequently changed: <strong>{most_changed_str}</strong></li>
        <li>Stable provisions (unchanged): <strong>{len(stats['most_stable'])}</strong></li>
        <li>New provisions (latest year): <strong>{len(stats['new_provisions'])}</strong></li>
        <li>Deleted provisions: <strong>{len(stats['deleted_provisions'])}</strong></li>
    </ul>

    {generate_reference_section(section_num)}

    <div class="legend">
        <strong>Legend:</strong>
        M=Modified | [Year]=Added |
        <span class="stable" style="padding: 2px 5px;">Stable</span>
        <span class="active" style="padding: 2px 5px;">Active</span>
        <span class="new" style="padding: 2px 5px;">New</span>
        <span class="deleted" style="padding: 2px 5px;">Deleted</span>
    </div>

    <h2>Change Frequency Table</h2>
    <table>
        <thead>
            <tr>
                <th>Provision</th>
                <th>Level</th>
                <th>Changes</th>
                <th>First Seen</th>
                <th>Last Modified</th>
                <th>Status</th>
                <th>Timeline</th>
            </tr>
        </thead>
        <tbody>
            {''.join(table_rows)}
        </tbody>
    </table>

    <h2>Most Frequently Changed Provisions</h2>
    {''.join(timeline_viz) if timeline_viz else '<p>No provisions have been modified.</p>'}

</body>
</html>
    """

    return html


def generate_csv_report(provision_history: dict, output_path: Path):
    """Generate CSV for further analysis."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'provision', 'level', 'total_changes', 'years_existed',
            'first_seen', 'last_modified', 'status', 'change_years'
        ])

        for path, data in sorted(provision_history.items()):
            change_years = [
                str(year) for year, info in sorted(data['history'].items())
                if info.get('status') == 'modified'
            ]

            years_existed = len([
                y for y, info in data['history'].items()
                if info.get('status') != 'missing'
            ])

            writer.writerow([
                format_path(path),
                data['level'],
                data['total_changes'],
                years_existed,
                data['first_seen'],
                data['last_modified'] or '-',
                data['status'],
                ';'.join(change_years)
            ])


# ============================================================================
# Main
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_changes.py <section_number>")
        print("Example: python analyze_changes.py 922")
        sys.exit(1)

    section_num = sys.argv[1]

    print(f"\n{'='*70}")
    print(f"Analyzing Historical Changes - 18 U.S.C. §{section_num}")
    print(f"{'='*70}\n")

    # Load all versions
    print("Loading versions...")
    versions = load_all_versions(section_num)

    if not versions:
        print(f"\nError: No versions found for section {section_num}")
        sys.exit(1)

    years = sorted(versions.keys())
    print(f"\nFound {len(versions)} versions: {', '.join(map(str, years))}\n")

    # Track provision history
    print("Tracking provision history across years...")
    provision_history = track_provision_history(versions)
    print(f"  Tracked {len(provision_history)} unique provisions\n")

    # Calculate statistics
    print("Calculating statistics...")
    stats = calculate_statistics(provision_history)

    # Create output directory
    output_dir = Path('data/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate HTML report
    print("Generating HTML report...")
    html = generate_html_report(section_num, provision_history, stats, years)
    html_path = output_dir / f'{section_num}_change_analysis.html'
    with open(html_path, 'w') as f:
        f.write(html)
    print(f"  ✓ {html_path}")

    # Generate CSV report
    print("Generating CSV report...")
    csv_path = output_dir / f'{section_num}_change_analysis.csv'
    generate_csv_report(provision_history, csv_path)
    print(f"  ✓ {csv_path}")

    print(f"\n{'='*70}")
    print("Analysis Complete")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
