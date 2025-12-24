"""
USC section parser - Parse XML and XHTML files on-the-fly.

This module contains the parsing logic extracted from scripts/extract_sections.py,
adapted for use in the Flask app to parse sections dynamically.
"""

import re
from pathlib import Path
from typing import List
from lxml import etree
from bs4 import BeautifulSoup


def parse_xml_section(xml_file: Path, section_num: str, year: int) -> dict:
    """
    Parse section from USLM XML format.

    Args:
        xml_file: Path to XML file
        section_num: Section number (e.g., "922")
        year: Year of the version

    Returns:
        Dictionary with parsed section data
    """
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

        # Extract num if present (direct child only)
        num_elem = elem.find(f'{{{ns["uslm"]}}}num')
        if num_elem is not None:
            result['num'] = ''.join(num_elem.itertext())

        # Extract heading if present (direct child only)
        heading_elem = elem.find(f'{{{ns["uslm"]}}}heading')
        if heading_elem is not None:
            result['heading'] = ''.join(heading_elem.itertext())

        # Extract text from direct child <chapeau> or <content> element
        # Subsections/paragraphs use <chapeau>, subparagraphs/clauses use <content>
        chapeau_elem = elem.find(f'{{{ns["uslm"]}}}chapeau')
        content_elem = elem.find(f'{{{ns["uslm"]}}}content')

        # Prefer chapeau if it exists, otherwise use content
        text_elem = chapeau_elem if chapeau_elem is not None else content_elem

        if text_elem is not None:
            result['text'] = ''.join(text_elem.itertext())
            # Extract references from the text element (refs can be nested in the text)
            refs = text_elem.findall(f'.//{{{ns["uslm"]}}}ref[@href]')
            if refs:
                result['refs'] = [
                    {'target': ref.get('href'), 'text': ref.text or ''}
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


class ParseContext:
    """Track rich hierarchical parsing state for context-aware parsing."""

    def __init__(self, section_num: str):
        self.section_base = f'/us/usc/t18/s{section_num}'
        self.parent_stack = {5: None, 6: None, 7: None, 8: None, 9: None}
        self.last_combined_css_level = None
        self.last_combined_deepest_level = None

    def should_continue_at_deeper_level(self, css_level: int) -> bool:
        """
        Check if current provision should continue at deeper level from combined number.

        Example: After (C)(i), provision (ii) at same CSS level should be at clause level.
        """
        return (
            css_level == self.last_combined_css_level and
            self.last_combined_css_level is not None and
            self.parent_stack.get(self.last_combined_deepest_level) is not None
        )


def _is_lowercase_roman(s: str) -> bool:
    """Check if string is a lowercase Roman numeral."""
    if not s:
        return False
    # Valid lowercase roman numeral characters
    return all(c in 'ivxlcdm' for c in s.lower()) and s.islower()


def _is_uppercase_roman(s: str) -> bool:
    """Check if string is an uppercase Roman numeral."""
    if not s:
        return False
    # Valid uppercase roman numeral characters
    return all(c in 'IVXLCDM' for c in s.upper()) and s.isupper()


def _get_level_from_number_pattern(clean_num: str, css_level: int, parent_stack: dict, prev_css_level: int) -> int:
    """
    Determine provision level from number pattern using CONTEXT.

    USC hierarchy:
    - Subsection: (a), (b), (z) - lowercase letter
    - Paragraph: (1), (2), (99) - digit
    - Subparagraph: (A), (B), (Z) - uppercase letter
    - Clause: (i), (ii), (xxx) - lowercase roman
    - Subclause: (I), (II), (XXX) - uppercase roman

    CONTEXT-AWARE: Single letters like (i), (x) can be subsections OR clauses
    depending on nesting depth. Check parent_stack to disambiguate.
    """
    # Check if digit (paragraph) - MUST be level 6, never anything else
    # USC law mandates: subsection=(letter), paragraph=(digit), subparagraph=(uppercase)
    if clean_num.isdigit():
        return 6

    # CRITICAL: If CSS level DECREASED from PREVIOUS element, trust CSS
    # This means we're popping back up the hierarchy (e.g., (A)→(i)→(ii) then (B))
    # Only applies to non-digit provisions (digits handled above)
    if prev_css_level > 0 and css_level < prev_css_level:
        # CSS decreased from previous - we're going back up
        return css_level

    # For single lowercase letters that could be roman numerals (i, v, x, l, c, d, m)
    # Use CONTEXT to decide: subsection (level 5) or clause (level 8)
    if len(clean_num) == 1 and clean_num.isalpha() and clean_num.islower():
        # Check if we're deeply nested (have parent at level 7+)
        # If so, treat as clause (level 8), otherwise subsection (level 5)
        for level in range(7, 10):
            if parent_stack.get(level):
                # Deep nesting detected - treat as clause
                return 8
        # No deep nesting - treat as subsection
        return 5

    # For single uppercase letters that could be roman numerals (I, V, X, L, C, D, M)
    # Use CONTEXT to decide: subparagraph (level 7) or subclause (level 9)
    if len(clean_num) == 1 and clean_num.isalpha() and clean_num.isupper():
        # Check if we're deeply nested (have parent at level 8+)
        # If so, treat as subclause (level 9), otherwise subparagraph (level 7)
        for level in range(8, 10):
            if parent_stack.get(level):
                # Deep nesting detected - treat as subclause
                return 9
        # No deep nesting - treat as subparagraph
        return 7

    # Multi-character lowercase roman (clause)
    if len(clean_num) > 1 and _is_lowercase_roman(clean_num):
        return 8

    # Multi-character uppercase roman (subclause)
    if len(clean_num) > 1 and _is_uppercase_roman(clean_num):
        return 9

    # Fallback: use CSS level
    return css_level


def _find_parent(target_level: int, parent_stack: dict):
    """Find parent at target level or closest level below target."""
    for level in range(target_level, 4, -1):
        if parent_stack.get(level):
            return parent_stack[level]
    return None


def _parse_provision_numbers(text: str) -> tuple:
    """
    Extract all provision numbers from beginning of text.

    Returns:
        Tuple of (numbers_list, remaining_text, is_repealed)
        - is_repealed: True if provision uses square brackets []

    Examples:
        "(p)(1) It shall..." → (["(p)", "(1)"], "It shall...", False)
        "[(v), (w) Repealed..." → (["(v)", "(w)"], "Repealed...", True)
        "(A) that, after..." → (["(A)"], "that, after...", False)
        "Text..." → ([], "Text...", False)
    """
    text = text.strip()
    numbers = []
    is_repealed = False

    # Handle square brackets at start (repealed provisions)
    if text.startswith('['):
        text = text[1:].strip()
        is_repealed = True

    # Find all consecutive provision numbers at start
    while True:
        # Match both () and [] brackets, with optional comma/space between
        match = re.match(r'^[\(]([a-zA-Z0-9]+)[\)][\s,]*', text)
        if not match:
            break
        numbers.append(f'({match.group(1)})')
        text = text[match.end():].strip()

    return numbers, text, is_repealed


def _extract_direct_text_only(elem) -> str:
    """
    Extract only direct text from element, not including nested elements.

    BeautifulSoup's .get_text() recursively gets ALL text including children.
    We need only the direct text to avoid duplication.
    """
    direct_texts = []
    for content in elem.children:
        if isinstance(content, str):
            # Direct text node
            direct_texts.append(content)
        elif content.name in ['em', 'a', 'span']:
            # Inline elements are part of this provision's text
            direct_texts.append(content.get_text())
        # Skip child <p> elements - they're child provisions

    return ' '.join(direct_texts).strip()


def _extract_refs(elem) -> list:
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


def _get_css_level_from_class(css_class) -> int:
    """Get hierarchy level from CSS class."""
    CLASS_TO_LEVEL = {
        'statutory-body': 5,
        'statutory-body-1em': 6,
        'statutory-body-2em': 7,
        'statutory-body-3em': 8,
        'statutory-body-4em': 9,
    }

    if isinstance(css_class, list):
        css_class = css_class[0] if css_class else ''

    return CLASS_TO_LEVEL.get(css_class, 5)


# Level to tag mapping (used by two-pass parser)
LEVEL_TO_TAG = {
    5: 'subsection',
    6: 'paragraph',
    7: 'subparagraph',
    8: 'clause',
    9: 'subclause',
}


def _extract_raw_elements(soup, section_header) -> List[dict]:
    """
    PASS 1: Extract all provision elements as flat list with metadata.

    Args:
        soup: BeautifulSoup object
        section_header: Section header element

    Returns:
        List of elements with css_level, nums, text, elem, and is_root_css metadata
    """
    elements = []

    # Extract all content until next section header
    for sibling in section_header.next_siblings:
        if sibling.name == 'h3' and 'section-head' in sibling.get('class', []):
            break

        if sibling.name == 'p':
            css_class = sibling.get('class', [])
            if isinstance(css_class, list):
                css_class_str = css_class[0] if css_class else ''
            else:
                css_class_str = css_class

            css_level = _get_css_level_from_class(css_class)

            # Check if this is root CSS level (statutory-body, not statutory-body-Xem)
            is_root_css = css_class_str == 'statutory-body'

            # Extract direct text and parse provision numbers
            text_content = _extract_direct_text_only(sibling)
            provision_nums, clean_text, is_repealed = _parse_provision_numbers(text_content)

            # Skip if no provision numbers (continuation text, not a provision)
            if not provision_nums:
                continue

            elements.append({
                'css_level': css_level,
                'nums': provision_nums,
                'text': clean_text,
                'elem': sibling,
                'is_root_css': is_root_css,  # Metadata for Pass 2
                'is_repealed': is_repealed   # Metadata for repealed provisions
            })

    return elements


def _attach_node(node, parent_stack, root_subsections):
    """Attach node to parent or root."""
    level = node['level']

    if level == 5:
        # Root subsection
        root_subsections.append(node)
        parent_stack[5] = node
    else:
        # Find parent at level-1
        parent = _find_parent(level - 1, parent_stack)
        if parent:
            child_key = LEVEL_TO_TAG[level] + 's'
            if child_key not in parent:
                parent[child_key] = []
            parent[child_key].append(node)

        parent_stack[level] = node

    # Clear deeper levels
    for l in range(level + 1, 10):
        parent_stack[l] = None


def _handle_combined_number(elem, next_elem, parent_stack, section_base, prev_css_level) -> List[dict]:
    """
    Process combined number like (p)(1) or repealed provisions like [(v), (w)].

    For repealed provisions (square brackets), all numbers are SIBLINGS at same level.
    For normal combined numbers, subsequent numbers are CHILDREN.

    Creates nodes for each number in the combined provision.
    """
    nodes = []
    is_repealed = elem.get('is_repealed', False)

    for i, num in enumerate(elem['nums']):
        clean_num = num.strip('()§. \xa0\u202f')

        if i == 0:
            # First number - use pattern, but DON'T use context for combined numbers
            # Combined numbers like (p)(1) at CSS 5 mean (p) is a subsection (shallow)
            # Create temporary empty parent_stack to disable context checking
            level = _get_level_from_number_pattern(clean_num, elem['css_level'], {}, prev_css_level)
        else:
            if is_repealed:
                # Repealed provisions: all numbers are SIBLINGS at same level
                level = _get_level_from_number_pattern(clean_num, elem['css_level'], {}, prev_css_level)
            else:
                # Normal combined: subsequent numbers are CHILDREN of previous
                level = nodes[-1]['level'] + 1
                # USC hierarchy only goes to level 9 (subclause)
                if level > 9:
                    level = 9  # Cap at deepest level

        # Only last number gets text (for normal combined numbers)
        # For repealed provisions, all share the same text
        if is_repealed:
            text = elem['text']  # All repealed provisions share same text
        else:
            text = elem['text'] if i == len(elem['nums']) - 1 else ''

        # Build ID
        if i == 0 or is_repealed:
            # First number OR repealed sibling - build from parent/section base
            parent = _find_parent(level - 1, parent_stack)
            if parent:
                provision_id = f"{parent['id']}/{clean_num}"
            else:
                provision_id = f"{section_base}/{clean_num}"
        else:
            # Child of previous number
            provision_id = f"{nodes[-1]['id']}/{clean_num}"

        node = {
            'id': provision_id,
            'tag': LEVEL_TO_TAG[level],
            'num': num,
            'text': text,
            'refs': _extract_refs(elem['elem']),
            'level': level
        }

        nodes.append(node)
        parent_stack[level] = node

    # Clear deeper levels
    deepest = nodes[-1]['level']
    for l in range(deepest + 1, 10):
        parent_stack[l] = None

    return nodes


def _handle_single_number(elem, parent_stack, section_base, prev_css_level) -> dict:
    """
    Process single provision number.

    Uses number pattern to determine level, but trusts root CSS level.
    """
    num = elem['nums'][0] if elem['nums'] else ''
    clean_num = num.strip('()§. \xa0\u202f')

    # For root CSS level, use pattern but IGNORE context (no parent_stack)
    # This prevents deep nesting from incorrectly treating root provisions as clauses
    if elem.get('is_root_css', False):
        level = _get_level_from_number_pattern(clean_num, elem['css_level'], {}, prev_css_level)
    else:
        # Determine level from number pattern with context
        level = _get_level_from_number_pattern(clean_num, elem['css_level'], parent_stack, prev_css_level)

    # Build ID
    parent = _find_parent(level - 1, parent_stack)
    if parent and clean_num:
        provision_id = f"{parent['id']}/{clean_num}"
    elif clean_num:
        provision_id = f"{section_base}/{clean_num}"
    else:
        provision_id = section_base

    node = {
        'id': provision_id,
        'tag': LEVEL_TO_TAG[level],
        'num': num,
        'text': elem['text'],
        'refs': _extract_refs(elem['elem']),
        'level': level
    }

    return node


def _build_hierarchy_from_elements(elements: List[dict], section_base: str) -> List[dict]:
    """
    PASS 2: Build hierarchical structure from flat element list.

    Uses look-ahead and number patterns to correctly build hierarchy.
    """
    root_subsections = []
    parent_stack = {}
    prev_css_level = 0  # Track previous element's CSS level

    for i, elem in enumerate(elements):
        # Look-ahead: get next element if exists
        next_elem = elements[i + 1] if i + 1 < len(elements) else None

        if len(elem['nums']) > 1:
            # Combined number - creates multiple nodes
            nodes = _handle_combined_number(elem, next_elem, parent_stack, section_base, prev_css_level)
            for node in nodes:
                _attach_node(node, parent_stack, root_subsections)
            # Update prev_css_level to the CHILD's level (last node in combined)
            prev_css_level = elem['css_level']
        else:
            # Single number - creates one node
            node = _handle_single_number(elem, parent_stack, section_base, prev_css_level)
            _attach_node(node, parent_stack, root_subsections)
            prev_css_level = elem['css_level']

    # Remove 'level' field from all nodes
    def remove_level(node):
        if 'level' in node:
            del node['level']
        for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
            for child in node.get(child_type, []):
                remove_level(child)

    for node in root_subsections:
        remove_level(node)

    return root_subsections


def parse_xhtml_section(xhtml_file: Path, section_num: str, year: int) -> dict:
    """
    Parse section from XHTML format, converting to same structure as XML.

    Args:
        xhtml_file: Path to XHTML file
        section_num: Section number (e.g., "922")
        year: Year of the version

    Returns:
        Dictionary with parsed section data
    """
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

    # Section base ID
    section_base = f'/us/usc/t18/s{section_num}'

    # PASS 1: Extract raw elements
    elements = _extract_raw_elements(soup, section_header)

    # PASS 2: Build hierarchy
    subsections = _build_hierarchy_from_elements(elements, section_base)

    # Build final structure matching XML format
    result = {
        'id': section_base,
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

    # Apply post-processing rules to fix known edge cases
    from .usc_rules import apply_post_parse_fixes
    result = apply_post_parse_fixes(result, section_num)

    return result
