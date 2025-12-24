#!/usr/bin/env python3
"""
Generate HTML view pages for each section showing statute text.
"""

import json
import re
from pathlib import Path
import html


def linkify_text(text: str, refs: list) -> str:
    """Convert references to HTML links."""
    if not text or not refs:
        return html.escape(text) if text else ''

    result = html.escape(text)

    for ref in refs:
        ref_text = ref.get('text', '')
        target = ref.get('target', '')

        if not ref_text or not target:
            continue

        # Escape the ref_text for matching in the escaped result
        escaped_ref = html.escape(ref_text)

        # Parse section number from target
        match = re.search(r'/t18/s(\d+)', target)
        if match:
            section_num = match.group(1)
            # Link to section view
            link = f'<a href="{section_num}.html" class="statute-ref" title="{html.escape(target)}">{escaped_ref}</a>'
            result = result.replace(escaped_ref, link)
        elif '/t18/' not in target:
            # External reference
            external_url = f'https://uscode.house.gov/view.xhtml?req={target.replace("/", ":")}'
            link = f'<a href="{external_url}" class="external-ref" target="_blank" title="{html.escape(target)}">{escaped_ref}</a>'
            result = result.replace(escaped_ref, link)

    return result


def render_provision(node: dict, level: int) -> str:
    """Recursively render a provision and its children."""
    tag = node.get('tag', '')
    num = node.get('num', '')
    text = node.get('text', '')
    refs = node.get('refs', [])

    # Level names for CSS classes
    level_names = {
        5: 'subsection',
        6: 'paragraph',
        7: 'subparagraph',
        8: 'clause',
        9: 'subclause'
    }

    level_class = level_names.get(level, 'provision')

    html_parts = []
    html_parts.append(f'<div class="{level_class}">')

    if num:
        html_parts.append(f'<span class="num">{html.escape(num)}</span> ')

    if text:
        html_parts.append(f'<span class="text">{linkify_text(text, refs)}</span>')

    # Render children
    for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
        children = node.get(child_type, [])
        for child in children:
            child_level = level + 1 if level > 0 else TAG_TO_LEVEL.get(child.get('tag', ''), 5)
            html_parts.append(render_provision(child, child_level))

    html_parts.append('</div>')

    return '\n'.join(html_parts)


TAG_TO_LEVEL = {
    'subsection': 5,
    'paragraph': 6,
    'subparagraph': 7,
    'clause': 8,
    'subclause': 9,
}


def render_statute_text(data: dict) -> str:
    """Render the complete statute text."""
    if not data:
        return '<p>No content available</p>'

    html_parts = []

    # Render all subsections
    for subsection in data.get('subsections', []):
        html_parts.append(render_provision(subsection, 5))

    # If no subsections, render text directly
    if not html_parts and data.get('text'):
        text = data.get('text', '')
        refs = data.get('refs', [])
        html_parts.append(f'<div class="section-text">{linkify_text(text, refs)}</div>')

    return '\n'.join(html_parts) if html_parts else '<p>No content available</p>'


def generate_section_view(section_num: str, sections_data_dir: Path, output_dir: Path):
    """Generate HTML page for a section with all versions."""

    section_dir = sections_data_dir / section_num
    if not section_dir.exists() or not section_dir.is_dir():
        return

    # Get all versions
    versions = {}
    for json_file in sorted(section_dir.glob('*.json')):
        try:
            year = int(json_file.stem)
            with open(json_file) as f:
                versions[year] = json.load(f)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  Error loading {json_file}: {e}")
            continue

    if not versions:
        return

    latest_year = max(versions.keys())
    latest_data = versions[latest_year]
    heading = latest_data.get('heading', 'Unknown')

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>18 U.S.C. § {section_num} - {heading}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.8;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        .controls {{
            background: #f5f5f5;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .controls select {{
            padding: 5px 10px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }}
        .controls a {{
            color: #0066cc;
            text-decoration: none;
            margin-left: 15px;
        }}
        .controls a:hover {{
            text-decoration: underline;
        }}

        /* Hierarchy levels */
        .subsection {{ margin: 20px 0; }}
        .paragraph {{ margin: 15px 0 15px 30px; }}
        .subparagraph {{ margin: 10px 0 10px 60px; }}
        .clause {{ margin: 8px 0 8px 90px; }}
        .subclause {{ margin: 5px 0 5px 120px; }}
        .section-text {{ margin: 20px 0; }}

        .num {{
            font-weight: 600;
            color: #0066cc;
        }}

        .text {{
            color: #333;
        }}

        /* Reference links */
        .statute-ref {{
            color: #0066cc;
            text-decoration: none;
            border-bottom: 1px dotted #0066cc;
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

        /* Comparison mode styles */
        .comparison-toggle {{
            padding: 6px 12px;
            background: #0066cc;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 15px;
        }}
        .comparison-toggle:hover {{
            background: #0052a3;
        }}
        .comparison-toggle.active {{
            background: #dc3545;
        }}
        .comparison-controls {{
            display: none;
            background: #fff3cd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }}
        .comparison-controls.active {{
            display: block;
        }}
        .comparison-controls select {{
            padding: 5px 10px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 3px;
            margin: 0 10px;
        }}
        #statute-text {{
            display: block;
        }}
        #statute-text.hidden {{
            display: none;
        }}
        .comparison-container {{
            display: none;
            margin-top: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            background: white;
            overflow-y: auto;
            max-height: 80vh;
        }}
        .comparison-container.active {{
            display: block;
        }}
        .comparison-header {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ddd;
        }}
        .comparison-header h3 {{
            flex: 1;
            margin: 0;
            color: #666;
        }}
        .diff-row {{
            display: flex;
            gap: 20px;
            min-height: 40px;
            align-items: stretch;
        }}
        .diff-cell {{
            flex: 1;
            padding: 10px;
            min-height: 40px;
            border-radius: 3px;
        }}
        .diff-cell.empty {{
            background: #fafafa;
            border: 1px dashed #ccc;
        }}
        .diff-added {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 8px;
            margin: 8px 0;
        }}
        .diff-deleted {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 8px;
            margin: 8px 0;
            opacity: 0.7;
        }}
        .diff-modified {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 8px;
            margin: 8px 0;
        }}
        .diff-unchanged {{
            opacity: 0.6;
        }}
        .diff-highlight {{
            background: #ffeb3b;
            padding: 2px 4px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <div>
            <label><strong>Version:</strong></label>
            <select id="version-select" onchange="switchVersion(this.value)">
'''

    # Add version options
    for year in sorted(versions.keys(), reverse=True):
        selected = 'selected' if year == latest_year else ''
        html += f'                <option value="{year}" {selected}>{year}</option>\n'

    html += f'''            </select>
        </div>
        <div>
            <button class="comparison-toggle" onclick="toggleComparison()">Compare Versions</button>
            <a href="../analysis/{section_num}_change_analysis.html">Analysis</a>
            <a href="../index.html">Index</a>
        </div>
    </div>

    <div class="comparison-controls" id="comparison-controls">
        <label><strong>Compare:</strong></label>
        <select id="compare-version1">
'''

    # Add version options for comparison
    for year in sorted(versions.keys()):
        html += f'            <option value="{year}">{year}</option>\n'

    html += '''        </select>
        <strong>with</strong>
        <select id="compare-version2">
'''

    # Add second set of version options
    for year in sorted(versions.keys(), reverse=True):
        selected = 'selected' if year == latest_year else ''
        html += f'            <option value="{year}" {selected}>{year}</option>\n'

    html += f'''        </select>
        <button onclick="showComparison()" style="margin-left: 15px; padding: 5px 15px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">Show Diff</button>
    </div>

    <h1>18 U.S.C. § {section_num} - {heading}</h1>

    <div id="statute-text">
{render_statute_text(latest_data)}
    </div>

    <div class="comparison-container" id="comparison-container">
        <div class="comparison-header">
            <h3 id="compare-left-title">Version 1</h3>
            <h3 id="compare-right-title">Version 2</h3>
        </div>
        <div id="comparison-content"></div>
    </div>

    <script>
        // Store all versions
        const versions = {json.dumps({str(k): v for k, v in versions.items()})};

        function switchVersion(year) {{
            const data = versions[year];
            if (!data) return;

            // Update heading
            document.querySelector('h1').textContent = `18 U.S.C. § {section_num} - ${{data.heading || 'Unknown'}}`;

            // Re-render statute text
            document.getElementById('statute-text').innerHTML = renderStatuteText(data);
        }}

        function renderStatuteText(data) {{
            if (!data || !data.subsections || data.subsections.length === 0) {{
                if (data.text) {{
                    return `<div class="section-text">${{escapeHtml(linkifyText(data.text, data.refs || []))}}</div>`;
                }}
                return '<p>No content available</p>';
            }}

            let html = '';
            for (const subsection of data.subsections) {{
                html += renderProvision(subsection, 5);
            }}
            return html;
        }}

        function renderProvision(node, level) {{
            const levelNames = {{5: 'subsection', 6: 'paragraph', 7: 'subparagraph', 8: 'clause', 9: 'subclause'}};
            const levelClass = levelNames[level] || 'provision';

            let html = `<div class="${{levelClass}}">`;

            if (node.num) {{
                html += `<span class="num">${{escapeHtml(node.num)}}</span> `;
            }}

            if (node.text) {{
                html += `<span class="text">${{linkifyText(node.text, node.refs || [])}}</span>`;
            }}

            // Render children
            const childTypes = ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses'];
            for (const childType of childTypes) {{
                const children = node[childType] || [];
                for (const child of children) {{
                    const childLevel = level + 1;
                    html += renderProvision(child, childLevel);
                }}
            }}

            html += '</div>';
            return html;
        }}

        function linkifyText(text, refs) {{
            if (!text) return '';
            let result = escapeHtml(text);

            for (const ref of refs) {{
                const refText = ref.text || '';
                const target = ref.target || '';
                if (!refText || !target) continue;

                const escapedRef = escapeHtml(refText);
                const match = target.match(/\\/t18\\/s(\\d+)/);

                if (match) {{
                    const sectionNum = match[1];
                    const link = `<a href="${{sectionNum}}.html" class="statute-ref" title="${{escapeHtml(target)}}">${{escapedRef}}</a>`;
                    result = result.replace(escapedRef, link);
                }} else if (!target.includes('/t18/')) {{
                    const externalUrl = `https://uscode.house.gov/view.xhtml?req=${{target.replace(/\\//g, ':')}}`;
                    const link = `<a href="${{externalUrl}}" class="external-ref" target="_blank" title="${{escapeHtml(target)}}">${{escapedRef}}</a>`;
                    result = result.replace(escapedRef, link);
                }}
            }}

            return result;
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // Comparison mode functions
        function toggleComparison() {{
            const controls = document.getElementById('comparison-controls');
            const toggle = document.querySelector('.comparison-toggle');
            const isActive = controls.classList.contains('active');

            if (isActive) {{
                // Close comparison mode
                controls.classList.remove('active');
                toggle.classList.remove('active');
                toggle.textContent = 'Compare Versions';
                document.getElementById('statute-text').classList.remove('hidden');
                document.getElementById('comparison-container').classList.remove('active');
            }} else {{
                // Enter comparison mode
                controls.classList.add('active');
                toggle.classList.add('active');
                toggle.textContent = '✕ Close Comparison';
            }}
        }}

        function showComparison() {{
            const year1 = document.getElementById('compare-version1').value;
            const year2 = document.getElementById('compare-version2').value;

            if (year1 === year2) {{
                alert('Please select two different versions to compare');
                return;
            }}

            // Hide normal view, show comparison
            document.getElementById('statute-text').classList.add('hidden');
            document.getElementById('comparison-container').classList.add('active');

            // Update titles
            document.getElementById('compare-left-title').textContent = `Version ${{year1}}`;
            document.getElementById('compare-right-title').textContent = `Version ${{year2}}`;

            // Generate comparison
            const data1 = versions[year1];
            const data2 = versions[year2];

            renderSideBySide(data1, data2, year1, year2);
        }}

        function buildProvisionTree(data) {{
            // Build flat tree of all provisions for diffing
            const tree = {{}};

            function traverse(node, path = '') {{
                const key = node.num || '';
                const fullPath = path ? `${{path}}/${{key}}` : key;

                if (key) {{
                    tree[fullPath] = {{
                        num: node.num,
                        text: node.text || '',
                        level: node.tag || 'section'
                    }};
                }}

                // Traverse children
                const childTypes = ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses'];
                for (const childType of childTypes) {{
                    const children = node[childType] || [];
                    for (const child of children) {{
                        traverse(child, fullPath || key);
                    }}
                }}
            }}

            if (data.subsections) {{
                for (const subsection of data.subsections) {{
                    traverse(subsection);
                }}
            }}

            return tree;
        }}

        function renderSideBySide(data1, data2, year1, year2) {{
            const tree1 = buildProvisionTree(data1);
            const tree2 = buildProvisionTree(data2);

            // Find all unique paths
            const allPaths = new Set([...Object.keys(tree1), ...Object.keys(tree2)]);
            const sortedPaths = Array.from(allPaths).sort();

            let html = '';

            for (const path of sortedPaths) {{
                const node1 = tree1[path];
                const node2 = tree2[path];

                if (!node1) {{
                    // Added in version 2 - empty left, content right
                    html += `<div class="diff-row">
                        <div class="diff-cell empty"></div>
                        <div class="diff-cell diff-added">
                            <span class="num">${{escapeHtml(node2.num)}}</span>
                            <span class="text">${{escapeHtml(node2.text)}}</span>
                        </div>
                    </div>`;
                }} else if (!node2) {{
                    // Deleted from version 1 - content left, empty right
                    html += `<div class="diff-row">
                        <div class="diff-cell diff-deleted">
                            <span class="num">${{escapeHtml(node1.num)}}</span>
                            <span class="text">${{escapeHtml(node1.text)}}</span>
                        </div>
                        <div class="diff-cell empty"></div>
                    </div>`;
                }} else if (node1.text !== node2.text) {{
                    // Modified - show both versions
                    html += `<div class="diff-row">
                        <div class="diff-cell diff-modified">
                            <span class="num">${{escapeHtml(node1.num)}}</span>
                            <span class="text">${{escapeHtml(node1.text)}}</span>
                        </div>
                        <div class="diff-cell diff-modified">
                            <span class="num">${{escapeHtml(node2.num)}}</span>
                            <span class="text">${{highlightDiff(node1.text, node2.text)}}</span>
                        </div>
                    </div>`;
                }} else {{
                    // Unchanged - show both (dimmed)
                    html += `<div class="diff-row">
                        <div class="diff-cell diff-unchanged">
                            <span class="num">${{escapeHtml(node1.num)}}</span>
                            <span class="text">${{escapeHtml(node1.text)}}</span>
                        </div>
                        <div class="diff-cell diff-unchanged">
                            <span class="num">${{escapeHtml(node2.num)}}</span>
                            <span class="text">${{escapeHtml(node2.text)}}</span>
                        </div>
                    </div>`;
                }}
            }}

            document.getElementById('comparison-content').innerHTML = html || '<p>No differences found</p>';
        }}

        function highlightDiff(text1, text2) {{
            // Simple word-level diff highlighting
            const words1 = text1.split(/\\s+/);
            const words2 = text2.split(/\\s+/);

            let result = '';
            const maxLen = Math.max(words1.length, words2.length);

            for (let i = 0; i < words2.length; i++) {{
                if (words1[i] !== words2[i]) {{
                    result += `<span class="diff-highlight">${{escapeHtml(words2[i])}}</span> `;
                }} else {{
                    result += escapeHtml(words2[i]) + ' ';
                }}
            }}

            return result.trim();
        }}
    </script>
</body>
</html>
'''

    # Write HTML file
    output_file = output_dir / f'{section_num}.html'
    with open(output_file, 'w') as f:
        f.write(html)


def main():
    sections_data_dir = Path('data/sections')
    output_dir = Path('data/views')
    output_dir.mkdir(exist_ok=True)

    print("\nGenerating section view pages...")
    print("=" * 60)

    # Get all section directories
    section_dirs = [d for d in sections_data_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    section_dirs.sort(key=lambda x: int(x.name))

    count = 0
    for section_dir in section_dirs:
        section_num = section_dir.name
        try:
            generate_section_view(section_num, sections_data_dir, output_dir)
            count += 1
            if count % 100 == 0:
                print(f"  Generated {count} pages...")
        except Exception as e:
            print(f"  Error generating § {section_num}: {e}")

    print(f"\n✓ Generated {count} section view pages")
    print(f"  Output: {output_dir}/")
    print("=" * 60)


if __name__ == '__main__':
    main()
