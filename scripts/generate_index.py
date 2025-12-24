#!/usr/bin/env python3
"""
Generate HTML index of all extracted Title 18 sections.
"""

import json
from pathlib import Path


def main():
    sections_dir = Path('data/sections')
    output_file = Path('data/index.html')

    # Collect all sections
    sections = []
    for section_dir in sorted(sections_dir.iterdir(), key=lambda x: int(x.name) if x.name.isdigit() else 0):
        if not section_dir.is_dir():
            continue

        section_num = section_dir.name

        # Get latest JSON
        json_files = list(section_dir.glob('*.json'))
        if not json_files:
            continue

        latest_json = max(json_files, key=lambda x: int(x.stem))

        try:
            with open(latest_json) as f:
                data = json.load(f)

            heading = data.get('heading', 'Unknown')
            year = int(latest_json.stem)

            # Check if we have analysis
            has_analysis = (Path(f'data/analysis/{section_num}_change_analysis.html')).exists()

            sections.append({
                'num': section_num,
                'heading': heading,
                'year': year,
                'has_analysis': has_analysis,
                'versions': len(json_files)
            })
        except Exception as e:
            print(f"Error processing {section_num}: {e}")
            continue

    # Sort by section number
    sections.sort(key=lambda x: int(x['num']) if x['num'].isdigit() else 0)

    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Title 18 U.S.C. - Crimes and Criminal Procedure</title>
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
        .stats {{
            background: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #0066cc;
            margin: 20px 0;
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
        .section-num {{
            font-family: 'Monaco', 'Courier New', monospace;
            font-weight: 600;
            color: #0066cc;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            background: #28a745;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <h1>Title 18 U.S.C. - Crimes and Criminal Procedure</h1>

    <div class="stats">
        <p><strong>Total sections extracted:</strong> {len(sections)}</p>
        <p><strong>Sections with analysis:</strong> {sum(1 for s in sections if s['has_analysis'])}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Section</th>
                <th>Heading</th>
                <th>Latest Version</th>
                <th>Versions</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
"""

    for section in sections:
        has_view = (Path(f'data/views/{section["num"]}.html')).exists()

        html += f"""
            <tr>
                <td class="section-num">§ {section['num']}</td>
                <td>{section['heading']}</td>
                <td>{section['year']}</td>
                <td>{section['versions']}</td>
                <td>
"""
        if has_view:
            html += f'<a href="views/{section["num"]}.html"><strong>View Text</strong></a>'
        else:
            html += '<span style="color:#999;">No view</span>'

        if section['has_analysis']:
            html += f' | <a href="analysis/{section["num"]}_change_analysis.html">Analysis</a>'

        html += """
                </td>
            </tr>
"""

    html += """
        </tbody>
    </table>

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em;">
        <p>Generated with USC Historical Analysis Tool</p>
    </footer>

</body>
</html>
"""

    # Write HTML
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✓ Generated index: {output_file}")
    print(f"  Total sections: {len(sections)}")
    print(f"  With analysis: {sum(1 for s in sections if s['has_analysis'])}")


if __name__ == '__main__':
    main()
