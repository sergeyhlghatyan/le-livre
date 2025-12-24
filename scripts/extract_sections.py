#!/usr/bin/env python3
"""
Extract sections 922 and 933 from Title 18 USC historical versions.
Outputs structured JSON preserving hierarchy, references, and metadata.
"""

import json
import sys
from pathlib import Path
from lxml import etree
from bs4 import BeautifulSoup


def extract_xml_section(xml_file: Path, section_num: str, year: int) -> dict:
    """Extract section from USLM XML format."""
    tree = etree.parse(xml_file)

    # Handle namespace
    ns = {'uslm': 'http://xml.house.gov/schemas/uslm/1.0'}
    section = tree.xpath(f'//uslm:section[@identifier="/us/usc/t18/s{section_num}"]', namespaces=ns)

    if not section:
        return None

    section = section[0]

    def parse_element(elem):
        """Recursively parse USLM element."""
        # Strip namespace from tag
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        result = {
            'id': elem.get('identifier', ''),
            'tag': tag,
        }

        # Extract num if present
        num_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}num')
        if num_elem is not None:
            result['num'] = num_elem.text

        # Extract heading if present
        heading_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}heading')
        if heading_elem is not None:
            result['heading'] = heading_elem.text

        # Extract content with references
        content_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}content')
        if content_elem is not None:
            result['text'] = ''.join(content_elem.itertext())
            refs = content_elem.findall('.//{http://xml.house.gov/schemas/uslm/1.0}ref[@href]')
            if refs:
                result['refs'] = [
                    {'target': ref.get('href'), 'text': ref.text}
                    for ref in refs
                ]

        # Recursively extract child elements
        for child_tag in ['subsection', 'paragraph', 'subparagraph', 'clause', 'subclause']:
            children = elem.findall(f'.//{{{ns["uslm"]}}}{child_tag}')
            # Only include direct children, not nested
            direct_children = [c for c in children if c.getparent() == elem]
            if direct_children:
                result[child_tag + 's'] = [parse_element(child) for child in direct_children]

        return result

    data = parse_element(section)
    data['metadata'] = {
        'year': year,
        'source': xml_file.name,
        'format': 'xml'
    }

    return data


def extract_xhtml_section(xhtml_file: Path, section_num: str, year: int) -> dict:
    """Extract section from XHTML format, converting to same structure as XML."""
    import re

    # Try multiple encodings
    content = None
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(xhtml_file, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if not content:
        raise ValueError(f"Could not decode {xhtml_file}")

    soup = BeautifulSoup(content, 'html.parser')

    # Find section header: <h3 class="section-head">&sect;922. ...
    section_header = soup.find('h3', class_='section-head', string=lambda s: s and f'§{section_num}.' in s)

    if not section_header:
        return None

    # CSS class to hierarchy level mapping
    CLASS_TO_LEVEL = {
        'statutory-body': 5,          # subsection
        'statutory-body-1em': 6,      # paragraph
        'statutory-body-2em': 7,      # subparagraph
        'statutory-body-3em': 8,      # clause
        'statutory-body-4em': 9,      # subclause
    }

    LEVEL_TO_TAG = {
        5: 'subsection',
        6: 'paragraph',
        7: 'subparagraph',
        8: 'clause',
        9: 'subclause',
    }

    # Extract all content until next section header
    elements = []
    for sibling in section_header.next_siblings:
        if sibling.name == 'h3' and 'section-head' in sibling.get('class', []):
            break
        if sibling.name == 'p':
            # Get CSS class to determine level
            css_class = sibling.get('class', [])
            if css_class:
                css_class = css_class[0] if isinstance(css_class, list) else css_class
                level = CLASS_TO_LEVEL.get(css_class)
                if level:
                    elements.append({
                        'element': sibling,
                        'level': level,
                        'tag': LEVEL_TO_TAG[level]
                    })

    def parse_provision_number(text: str) -> str:
        """Extract (a), (1), (A) from beginning of text."""
        text = text.strip()
        match = re.match(r'^\(([a-zA-Z0-9]+)\)', text)
        return f'({match.group(1)})' if match else ''

    def extract_refs(elem) -> list:
        """Extract references from <a> tags."""
        refs = []
        for link in elem.find_all('a'):
            href = link.get('href', '')
            if href:
                refs.append({
                    'target': href,
                    'text': link.get_text()
                })
        return refs

    def build_tree(elements: list) -> list:
        """Build hierarchical tree from flat list of elements."""
        if not elements:
            return []

        # Parse all elements into provisional nodes
        nodes = []
        for item in elements:
            elem = item['element']
            text_content = elem.get_text().strip()

            node = {
                'id': f'/us/usc/t18/s{section_num}',  # Will be updated with full path
                'tag': item['tag'],
                'num': parse_provision_number(text_content),
                'text': text_content,
                'refs': extract_refs(elem),
                'level': item['level']
            }
            nodes.append(node)

        # Build parent-child relationships
        root_subsections = []
        parent_stack = {5: None, 6: None, 7: None, 8: None, 9: None}

        for node in nodes:
            level = node['level']

            if level == 5:
                # Top level subsection
                root_subsections.append(node)
                parent_stack[5] = node
                # Clear lower levels
                for l in range(6, 10):
                    parent_stack[l] = None
            else:
                # Find parent (next higher level)
                parent = None
                for parent_level in range(level - 1, 4, -1):
                    if parent_stack.get(parent_level):
                        parent = parent_stack[parent_level]
                        break

                if parent:
                    # Add as child to parent
                    child_key = LEVEL_TO_TAG[level] + 's'  # e.g., 'paragraphs'
                    if child_key not in parent:
                        parent[child_key] = []
                    parent[child_key].append(node)

                # Update parent stack
                parent_stack[level] = node
                # Clear lower levels
                for l in range(level + 1, 10):
                    parent_stack[l] = None

            # Remove 'level' from final output
            del node['level']

        return root_subsections

    subsections = build_tree(elements)

    # Build final structure matching XML format
    return {
        'id': f'/us/usc/t18/s{section_num}',
        'tag': 'section',
        'num': f'§\u202f{section_num}.',
        'heading': section_header.get_text().replace('§', '').strip().replace(section_num + '.', '').strip(),
        'subsections': subsections,
        'metadata': {
            'year': year,
            'source': xhtml_file.name,
            'format': 'xhtml',
        }
    }


def extract_all_xml_sections(xml_file: Path, year: int, output_dir: Path) -> int:
    """Extract all sections from an XML file."""
    tree = etree.parse(xml_file)
    ns = {'uslm': 'http://xml.house.gov/schemas/uslm/1.0'}

    sections = tree.xpath('//uslm:section', namespaces=ns)
    print(f"  Found {len(sections)} sections")

    extracted = 0
    for section_elem in sections:
        identifier = section_elem.get('identifier', '')

        # Extract section number from identifier
        import re
        match = re.search(r'/s(\d+[a-z]?)', identifier)
        if not match:
            continue

        section_num = match.group(1)
        section_dir = output_dir / section_num
        section_dir.mkdir(parents=True, exist_ok=True)

        # Parse the section
        def parse_element(elem):
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            result = {
                'id': elem.get('identifier', ''),
                'tag': tag,
            }

            num_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}num')
            if num_elem is not None:
                result['num'] = ''.join(num_elem.itertext())

            heading_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}heading')
            if heading_elem is not None:
                result['heading'] = ''.join(heading_elem.itertext())

            content_elem = elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}content')
            if content_elem is not None:
                result['text'] = ''.join(content_elem.itertext())
                refs = content_elem.findall('.//{http://xml.house.gov/schemas/uslm/1.0}ref[@href]')
                if refs:
                    result['refs'] = [
                        {'target': ref.get('href'), 'text': ref.text or ''}
                        for ref in refs
                    ]

            for child_tag in ['subsection', 'paragraph', 'subparagraph', 'clause', 'subclause']:
                children = elem.findall(f'.//{{{ns["uslm"]}}}{child_tag}')
                direct_children = [c for c in children if c.getparent() == elem]
                if direct_children:
                    result[child_tag + 's'] = [parse_element(child) for child in direct_children]

            return result

        data = parse_element(section_elem)
        data['metadata'] = {
            'year': year,
            'source': xml_file.name,
            'format': 'xml'
        }

        output_file = section_dir / f'{year}.json'
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        extracted += 1

    return extracted


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract USC sections from XML/XHTML files')
    parser.add_argument('--all', action='store_true', help='Extract all sections (XML only)')
    parser.add_argument('--sections', nargs='+', default=['922', '933'], help='Specific sections to extract')
    args = parser.parse_args()

    base_dir = Path('data/raw/uslm')
    output_dir = Path('data/sections')

    years_config = {
        2024: {'format': 'xml', 'file': '2024/usc18.xml'},
        2022: {'format': 'xml', 'file': '2022/usc18.xml'},
        2018: {'format': 'xhtml', 'file': '2018/2018/2018usc18.htm'},
        2013: {'format': 'xhtml', 'file': '2013/2013/2013usc18.htm'},
        2006: {'format': 'xhtml', 'file': '2006/2006/2006usc18.htm'},
        2000: {'format': 'xhtml', 'file': '2000/2000/2000usc18.htm'},
        1994: {'format': 'xhtml', 'file': '1994/1994/1994usc18.htm'},
    }

    if args.all:
        # Extract all sections (XML only for now)
        print(f"\n{'='*60}")
        print("Extracting ALL Title 18 Sections")
        print(f"{'='*60}\n")

        for year, config in sorted(years_config.items(), reverse=True):
            if config['format'] != 'xml':
                continue  # Skip XHTML for bulk extraction

            file_path = base_dir / config['file']
            if not file_path.exists():
                print(f"✗ {year}: File not found - {file_path}")
                continue

            try:
                print(f"{year}:")
                count = extract_all_xml_sections(file_path, year, output_dir)
                print(f"  ✓ Extracted {count} sections\n")
            except Exception as e:
                print(f"  ✗ Error: {e}\n")

        print(f"{'='*60}")
        print("Bulk extraction complete")
        print(f"{'='*60}\n")
        return

    # Extract specific sections
    sections = args.sections

    for section_num in sections:
        section_dir = output_dir / section_num
        section_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Extracting Section {section_num}")
        print(f"{'='*60}")

        for year, config in sorted(years_config.items(), reverse=True):
            file_path = base_dir / config['file']

            if not file_path.exists():
                print(f"✗ {year}: File not found - {file_path}")
                continue

            try:
                if config['format'] == 'xml':
                    data = extract_xml_section(file_path, section_num, year)
                else:
                    data = extract_xhtml_section(file_path, section_num, year)

                if data:
                    output_file = section_dir / f'{year}.json'
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"✓ {year}: {output_file}")
                else:
                    print(f"✗ {year}: Section not found")

            except Exception as e:
                print(f"✗ {year}: Error - {e}")

    print(f"\n{'='*60}")
    print("Extraction complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
