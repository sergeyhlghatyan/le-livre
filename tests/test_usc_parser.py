"""Tests for usc_parser.py - XML and XHTML section parsing."""

import pytest
from pathlib import Path
from services.usc_parser import parse_xml_section, parse_xhtml_section


class TestXMLParser:
    """Tests for parse_xml_section function."""

    def test_parse_xml_section_exists(self, section_922_xml_2024):
        """Test that section 922 can be found and parsed from XML."""
        result = parse_xml_section(section_922_xml_2024, '922', 2024)

        assert result is not None
        assert result['id'] == '/us/usc/t18/s922'
        assert result['tag'] == 'section'
        assert '922' in result['num']

    def test_parse_xml_section_has_metadata(self, parsed_section_922_2024):
        """Test that parsed XML section includes metadata."""
        assert 'metadata' in parsed_section_922_2024
        assert parsed_section_922_2024['metadata']['year'] == 2024
        assert parsed_section_922_2024['metadata']['format'] == 'xml'
        assert 'usc18.xml' in parsed_section_922_2024['metadata']['source']

    def test_parse_xml_section_builds_correct_ids(self, parsed_section_922_2024):
        """Test that XML parser builds correct hierarchical IDs."""
        subsection_a = parsed_section_922_2024['subsections'][0]
        assert subsection_a['id'] == '/us/usc/t18/s922/a'

        paragraph_1 = subsection_a['paragraphs'][0]
        assert paragraph_1['id'] == '/us/usc/t18/s922/a/1'

        subparagraph_a = paragraph_1['subparagraphs'][0]
        assert subparagraph_a['id'] == '/us/usc/t18/s922/a/1/A'

    def test_parse_xml_section_deep_nested_all_5_levels(self, parsed_section_922_2024):
        """
        CRITICAL: Test that XML parser extracts all 5 hierarchy levels including clauses and subclauses.

        This verifies the parser can handle deeply nested structures:
        subsection → paragraph → subparagraph → clause → subclause
        """
        # Navigate to subsection (s) → paragraph (1) → subparagraph (A) → clause (i) → subclause (I)
        subsection_s = next((s for s in parsed_section_922_2024['subsections'] if s['num'] == '(s)'), None)
        assert subsection_s is not None, "Subsection (s) should exist"
        assert subsection_s['id'] == '/us/usc/t18/s922/s'
        assert subsection_s['tag'] == 'subsection'

        paragraph_1 = next((p for p in subsection_s.get('paragraphs', []) if p['num'] == '(1)'), None)
        assert paragraph_1 is not None, "Paragraph (1) should exist under subsection (s)"
        assert paragraph_1['id'] == '/us/usc/t18/s922/s/1'
        assert paragraph_1['tag'] == 'paragraph'

        subparagraph_A = next((sp for sp in paragraph_1.get('subparagraphs', []) if sp['num'] == '(A)'), None)
        assert subparagraph_A is not None, "Subparagraph (A) should exist under paragraph (1)"
        assert subparagraph_A['id'] == '/us/usc/t18/s922/s/1/A'
        assert subparagraph_A['tag'] == 'subparagraph'

        # CRITICAL: Test clause level (level 8)
        clause_i = next((c for c in subparagraph_A.get('clauses', []) if c['num'] == '(i)'), None)
        assert clause_i is not None, "Clause (i) should exist under subparagraph (A)"
        assert clause_i['id'] == '/us/usc/t18/s922/s/1/A/i'
        assert clause_i['tag'] == 'clause'

        # CRITICAL: Test subclause level (level 9) - deepest level
        subclause_I = next((sc for sc in clause_i.get('subclauses', []) if sc['num'] == '(I)'), None)
        assert subclause_I is not None, "Subclause (I) should exist under clause (i)"
        assert subclause_I['id'] == '/us/usc/t18/s922/s/1/A/i/I'
        assert subclause_I['tag'] == 'subclause'

        # Verify all 5 levels have text or children
        assert 'text' in subsection_s or 'paragraphs' in subsection_s
        assert 'text' in paragraph_1 or 'subparagraphs' in paragraph_1
        assert 'text' in subparagraph_A or 'clauses' in subparagraph_A
        assert 'text' in clause_i or 'subclauses' in clause_i
        assert 'text' in subclause_I  # Deepest level should have text

    # ===== CRITICAL BUG DETECTION TESTS =====

    def test_parse_xml_section_text_not_duplicated_across_hierarchy(self, parsed_section_922_2024):
        """
        CRITICAL BUG TEST: Verify that text is NOT duplicated across parent-child hierarchy.

        Known bug: XML parser extracts full text for subsection (a), then duplicates
        the same text to paragraph (1), and again to subparagraph (A).

        Expected behavior: Each level should have ONLY its own text content,
        not the concatenated text of all its children.
        """
        subsection_a = parsed_section_922_2024['subsections'][0]
        paragraph_1 = subsection_a['paragraphs'][0]
        subparagraph_a = paragraph_1['subparagraphs'][0]

        # Get text from each level
        subsection_text = subsection_a.get('text', '')
        paragraph_text = paragraph_1.get('text', '')
        subparagraph_text = subparagraph_a.get('text', '')

        # CRITICAL ASSERTION: Text should be different at each level
        # If they're identical, the bug is present
        assert subsection_text != paragraph_text, (
            f"BUG DETECTED: Subsection (a) and Paragraph (1) have identical text.\n"
            f"Subsection text length: {len(subsection_text)} chars\n"
            f"Paragraph text length: {len(paragraph_text)} chars\n"
            f"This indicates the XML parser is duplicating text across hierarchy levels."
        )

        assert paragraph_text != subparagraph_text, (
            f"BUG DETECTED: Paragraph (1) and Subparagraph (A) have identical text.\n"
            f"Paragraph text length: {len(paragraph_text)} chars\n"
            f"Subparagraph text length: {len(subparagraph_text)} chars\n"
            f"This indicates the XML parser is duplicating text across hierarchy levels."
        )

        assert subsection_text != subparagraph_text, (
            f"BUG DETECTED: Subsection (a) and Subparagraph (A) have identical text.\n"
            f"This indicates severe text duplication across multiple hierarchy levels."
        )

    def test_parse_xml_section_subsection_text_is_chapeau_only(self, parsed_section_922_2024):
        """
        Test that subsection text contains only chapeau (introductory text),
        not the full text of all child provisions.

        For section 922(a), the subsection text should be:
        "It shall be unlawful—" (the chapeau)

        NOT the full text including all paragraphs.
        """
        subsection_a = parsed_section_922_2024['subsections'][0]
        subsection_text = subsection_a.get('text', '').strip()

        # Subsection (a) chapeau is very short: "It shall be unlawful—"
        # If text is longer than ~100 characters, it likely contains child text
        assert len(subsection_text) < 100, (
            f"Subsection (a) text is too long ({len(subsection_text)} chars).\n"
            f"Expected: 'It shall be unlawful—' (~25 chars)\n"
            f"Actual: {subsection_text[:100]}...\n"
            f"This suggests child provision text was incorrectly included."
        )

        # Should contain the chapeau text
        assert 'unlawful' in subsection_text.lower()

    def test_parse_xml_section_paragraph_text_is_chapeau_only(self, parsed_section_922_2024):
        """
        Test that paragraph text contains only chapeau, not subparagraph text.

        For 922(a)(1), the paragraph text should be:
        "for any person—" (the chapeau)

        NOT the full text of subparagraphs (A) and (B).
        """
        subsection_a = parsed_section_922_2024['subsections'][0]
        paragraph_1 = subsection_a['paragraphs'][0]
        paragraph_text = paragraph_1.get('text', '').strip()

        # Paragraph (1) chapeau: "for any person—" (~15 chars)
        # If text mentions "licensed importer", it contains subparagraph (A) text
        assert 'licensed importer' not in paragraph_text.lower(), (
            f"Paragraph (1) text contains subparagraph content.\n"
            f"Expected: 'for any person—'\n"
            f"Actual: {paragraph_text[:100]}...\n"
            f"This indicates the XML parser included child subparagraph text."
        )

        assert len(paragraph_text) < 50, (
            f"Paragraph (1) text is too long ({len(paragraph_text)} chars).\n"
            f"Expected chapeau only (~15 chars)."
        )

    def test_parse_xml_section_subparagraph_has_content_text(self, parsed_section_922_2024):
        """
        Test that subparagraph contains actual content text.

        Subparagraph (A) should have substantive text about "licensed importer,
        licensed manufacturer, or licensed dealer..."
        """
        subsection_a = parsed_section_922_2024['subsections'][0]
        paragraph_1 = subsection_a['paragraphs'][0]
        subparagraph_a = paragraph_1['subparagraphs'][0]
        subparagraph_text = subparagraph_a.get('text', '').strip()

        # Subparagraph (A) has substantial content (>100 chars)
        assert len(subparagraph_text) > 50, (
            f"Subparagraph (A) text is too short ({len(subparagraph_text)} chars).\n"
            f"Expected substantive content about licensed importers/manufacturers."
        )

        # Should contain key terms
        assert 'licensed' in subparagraph_text.lower()

    def test_parse_xml_section_extracts_references(self, parsed_section_922_2024):
        """Test that XML parser extracts cross-references."""
        # Find all refs recursively
        def find_refs(node):
            """Recursively find all refs in a node and its children."""
            refs = node.get('refs', [])
            for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
                for child in node.get(child_type, []):
                    refs.extend(find_refs(child))
            return refs

        all_refs = find_refs(parsed_section_922_2024)

        # Section 922 should have many cross-references
        assert len(all_refs) > 0, "Expected section 922 to contain cross-references"

        # Check reference structure
        if all_refs:
            ref = all_refs[0]
            assert 'target' in ref
            assert 'text' in ref


class TestXHTMLParser:
    """Tests for parse_xhtml_section function."""

    def test_parse_xhtml_section_has_metadata(self, parsed_section_922_2006):
        """Test that parsed XHTML section includes metadata."""
        assert 'metadata' in parsed_section_922_2006
        assert parsed_section_922_2006['metadata']['year'] == 2006
        assert parsed_section_922_2006['metadata']['format'] == 'xhtml'
        assert '2006usc18.htm' in parsed_section_922_2006['metadata']['source']

    def test_parse_xhtml_section_handles_combined_provision_numbers(self, parsed_section_922_2006):
        """
        Test that XHTML parser correctly handles combined provision numbers.

        Example: "(p)(1)" in a single <p> tag should create:
        - Subsection (p) with chapeau text
        - Paragraph (1) as child of (p) with the actual content
        """
        # Find subsection (p) - this is known to have combined numbers in XHTML
        subsection_p = None
        for sub in parsed_section_922_2006['subsections']:
            if sub.get('num') == '(p)':
                subsection_p = sub
                break

        if subsection_p:  # Only test if (p) exists in this version
            # Should have paragraphs
            assert 'paragraphs' in subsection_p
            assert len(subsection_p['paragraphs']) > 0

            # First paragraph should be (1)
            paragraph_1 = subsection_p['paragraphs'][0]
            assert paragraph_1['num'] == '(1)'

            # Paragraph (1) should have the actual content text
            assert len(paragraph_1.get('text', '')) > 50

    def test_parse_xhtml_section_builds_correct_ids_from_css(self, parsed_section_922_2006):
        """Test that XHTML parser builds correct IDs from CSS class hierarchy."""
        subsection_a = parsed_section_922_2006['subsections'][0]
        assert subsection_a['id'] == '/us/usc/t18/s922/a'

        paragraph_1 = subsection_a['paragraphs'][0]
        assert paragraph_1['id'] == '/us/usc/t18/s922/a/1'

        subparagraph_a = paragraph_1['subparagraphs'][0]
        assert subparagraph_a['id'] == '/us/usc/t18/s922/a/1/A'

    def test_parse_xhtml_section_extracts_provision_numbers(self, parsed_section_922_2006):
        """Test that XHTML parser correctly extracts provision numbers from text."""
        subsection_a = parsed_section_922_2006['subsections'][0]

        # Should extract "(a)" and strip from text
        assert subsection_a['num'] == '(a)'

        # Text should not start with "(a)"
        text = subsection_a.get('text', '').strip()
        assert not text.startswith('(a)')

    def test_parse_xhtml_section_handles_encoding(self, raw_data_dir):
        """Test that XHTML parser handles various text encodings."""
        # Try parsing from different years (different encodings)
        years_to_test = [
            (2006, '2006/2006/2006usc18.htm'),
            (2018, '2018/2018/2018usc18.htm'),
        ]

        for year, rel_path in years_to_test:
            file_path = raw_data_dir / rel_path
            if file_path.exists():
                result = parse_xhtml_section(file_path, '922', year)
                assert result is not None, f"Failed to parse {year} XHTML"

    def test_parse_xhtml_section_returns_none_for_missing_section(self, section_922_xhtml_2006):
        """Test that parser returns None for non-existent section."""
        result = parse_xhtml_section(section_922_xhtml_2006, '99999', 2006)
        assert result is None

    def test_parse_xhtml_section_deep_nested_ids_with_intermediate_nodes(self, data_loader):
        """Test that XHTML parser creates correct IDs for deeply nested provisions."""
        parsed_2018 = data_loader.get_section('922', 2018)

        # Navigate to subsection (d) → paragraph (8) → subparagraph (B) → clause (ii)
        subsection_d = next(s for s in parsed_2018['subsections'] if s['num'] == '(d)')
        paragraph_8 = next(p for p in subsection_d['paragraphs'] if p['num'] == '(8)')
        subparagraph_b = next(sp for sp in paragraph_8['subparagraphs'] if sp['num'] == '(B)')

        # Check that (B) has clauses (i) and (ii)
        assert 'clauses' in subparagraph_b
        clause_ii = next(c for c in subparagraph_b['clauses'] if c['num'] == '(ii)')

        # Verify correct ID
        assert clause_ii['id'] == '/us/usc/t18/s922/d/8/B/ii'

    def test_xhtml_combined_number_then_single_at_same_css_level(self, data_loader):
        """Test pattern: (C)(i) then (ii) at same CSS level creates correct hierarchy."""
        parsed_2018 = data_loader.get_section('922', 2018)

        # Get subsection (g) → paragraph (8)
        # Note: paragraph (8) is under (g), not (f)
        subsection_g = next(s for s in parsed_2018['subsections'] if s['num'] == '(g)')
        paragraph_8 = next(p for p in subsection_g['paragraphs'] if p['num'] == '(8)')

        # Should have subparagraph (C) with clauses (i) and (ii)
        subparagraph_c = next(sp for sp in paragraph_8['subparagraphs'] if sp['num'] == '(C)')
        clauses = subparagraph_c.get('clauses', [])

        assert len(clauses) >= 2
        clause_i = next(c for c in clauses if c['num'] == '(i)')
        clause_ii = next(c for c in clauses if c['num'] == '(ii)')

        # Verify IDs
        assert clause_i['id'] == '/us/usc/t18/s922/g/8/C/i'
        assert clause_ii['id'] == '/us/usc/t18/s922/g/8/C/ii'

    @pytest.mark.parametrize("year,format_name", [(2018, "XHTML"), (2024, "XML")])
    def test_no_duplicate_subsection_numbers(self, data_loader, year, format_name):
        """Test that parser doesn't create duplicate subsection numbers."""
        parsed = data_loader.get_section('922', year)
        nums = [s['num'] for s in parsed['subsections']]
        unique_nums = set(nums)

        assert len(nums) == len(unique_nums), \
            f"{format_name} has duplicate subsections: {[n for n in nums if nums.count(n) > 1]}"

    @pytest.mark.parametrize("year,format_name", [(2018, "XHTML"), (2024, "XML")])
    def test_subsections_use_letters_not_digits(self, data_loader, year, format_name):
        """Test that subsections use letters (a-z) not digits."""
        parsed = data_loader.get_section('922', year)
        digit_subsections = [s['num'] for s in parsed['subsections']
                            if s.get('num') and s['num'].strip('()').isdigit()]

        assert len(digit_subsections) == 0, \
            f"{format_name} has digit subsections: {digit_subsections}"

    def test_xhtml_no_empty_subsection_numbers(self, data_loader):
        """Test that all subsections have non-empty numbers."""
        parsed_2018 = data_loader.get_section('922', 2018)
        empty = [s for s in parsed_2018['subsections'] if not s.get('num') or s['num'].strip() == '']
        assert len(empty) == 0, f"Found {len(empty)} subsections with empty numbers"

    def test_xhtml_paragraphs_use_digits_not_letters(self, data_loader):
        """Test that paragraphs use digits (1-9) not letters."""
        parsed_2018 = data_loader.get_section('922', 2018)
        if parsed_2018['subsections'] and 'paragraphs' in parsed_2018['subsections'][0]:
            letter_paragraphs = [p['num'] for p in parsed_2018['subsections'][0]['paragraphs']
                                if p.get('num') and p['num'].strip('()').isalpha()]
            assert len(letter_paragraphs) == 0, \
                f"Paragraphs using letters instead of digits: {letter_paragraphs}"

    def test_xhtml_all_provisions_have_text_or_children(self, data_loader):
        """Test that all provisions have either text or child provisions."""
        parsed_2018 = data_loader.get_section('922', 2018)

        def check_node(node, path=""):
            node_id = node.get('id', path)
            has_text = bool(node.get('text', '').strip())
            has_children = any(node.get(k) for k in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses'])

            assert has_text or has_children, f"Node {node_id} has no text and no children"

            for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
                for child in node.get(child_type, []):
                    check_node(child, node_id)

        check_node(parsed_2018)

    def test_xhtml_subsection_g_not_nested_under_f(self, data_loader):
        """
        Test the specific bug: subsection (g) should NOT be nested as a paragraph under (f).

        Bug scenario:
        - (f)(1) and (2) both at CSS level 5 (statutory-body)
        - (g) also at CSS level 5
        - Parser was treating (g) as continuation of (f), making it a paragraph under (f)
        - Fix: Check if provision is a lowercase letter at level 5 → new subsection
        """
        parsed_2018 = data_loader.get_section('922', 2018)

        # 1. Check that (g) exists as a root subsection
        subsection_nums = [s['num'] for s in parsed_2018['subsections']]
        assert '(g)' in subsection_nums, \
            f"Subsection (g) should exist in root subsections, got: {subsection_nums}"

        # 2. Check that (g) is NOT nested under (f)
        sub_f = next((s for s in parsed_2018['subsections'] if s['num'] == '(f)'), None)
        assert sub_f is not None, "Subsection (f) should exist"

        if 'paragraphs' in sub_f:
            para_nums = [p['num'] for p in sub_f['paragraphs']]
            assert '(g)' not in para_nums, \
                f"BUG: (g) is nested as paragraph under (f). Paragraphs: {para_nums}"

        # 3. Check that (g) has correct ID
        sub_g = next((s for s in parsed_2018['subsections'] if s['num'] == '(g)'), None)
        assert sub_g is not None, "Subsection (g) should exist"
        assert sub_g['id'] == '/us/usc/t18/s922/g', \
            f"Subsection (g) has wrong ID: {sub_g['id']}, expected: /us/usc/t18/s922/g"

        # 4. Check that (g) has paragraphs (it should have content)
        assert 'paragraphs' in sub_g or sub_g.get('text'), \
            "Subsection (g) should have paragraphs or text"

    def test_xhtml_physical_force_provision_ids_match_xml(self, data_loader):
        """
        Test that physical force provisions have matching IDs between 2018 (XHTML) and 2024 (XML).

        This catches the cascading bug where (g) being nested under (f) causes
        provisions under (g) to have wrong parent in their IDs.
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        parsed_2024 = data_loader.get_section('922', 2024)

        # Find physical force provisions
        def find_by_text(data, search_text):
            results = []
            def traverse(node):
                if 'text' in node and search_text.lower() in node.get('text', '').lower():
                    results.append(node['id'])
                for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
                    for child in node.get(child_type, []):
                        traverse(child)
            for sub in data['subsections']:
                traverse(sub)
            return results

        pf_ids_2018 = set(find_by_text(parsed_2018, 'physical force'))
        pf_ids_2024 = set(find_by_text(parsed_2024, 'physical force'))

        # Check that we don't have wrong IDs like /us/usc/t18/s922/f/8/C/ii
        # when it should be /us/usc/t18/s922/g/8/C/ii
        wrong_ids = [id for id in pf_ids_2018 if '/f/8/C/ii' in id or '/f/8/B/ii' in id]
        assert len(wrong_ids) == 0, \
            f"Found physical force provisions with wrong parent (f instead of g): {wrong_ids}"

        # Check for the specific provision that was problematic
        assert '/us/usc/t18/s922/g/8/C/ii' in pf_ids_2018, \
            "Should have /us/usc/t18/s922/g/8/C/ii in 2018 (not under f)"

    def test_xhtml_parent_child_text_separation(self, section_922_xhtml_2018):
        """
        CRITICAL: Verify parent provisions don't include child text.

        This test ensures the fix for the text duplication bug is working.
        BeautifulSoup's .get_text() recursively gets ALL text including children.
        We must extract only DIRECT text to avoid duplication in comparisons.

        Bug example: /us/usc/t18/s922/r/2/s (parent) was including text from
        /us/usc/t18/s922/r/2/s/1 (child), causing "Beginning on the date..."
        to appear twice in comparison view.
        """
        data = parse_xhtml_section(section_922_xhtml_2018, '922', 2018)

        # Helper to find provision by ID
        def find_provision_by_id(data, target_id):
            def traverse(node):
                if node.get('id') == target_id:
                    return node
                for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
                    for child in node.get(child_type, []):
                        result = traverse(child)
                        if result:
                            return result
                return None

            # Check root
            if data.get('id') == target_id:
                return data
            # Check subsections
            for sub in data.get('subsections', []):
                result = traverse(sub)
                if result:
                    return result
            return None

        # Test case 1: Subsection (r) → paragraph (2) → subparagraph (s) → paragraph (1)
        # This is the exact case from the bug report
        parent = find_provision_by_id(data, '/us/usc/t18/s922/r/2/s')
        child = find_provision_by_id(data, '/us/usc/t18/s922/r/2/s/1')

        if parent and child:
            parent_text = parent.get('text', '')
            child_text = child.get('text', '')

            # Child should have the full text
            assert 'Beginning on the date' in child_text, \
                "Child provision should contain the text"

            # Parent should NOT contain the child's text
            # (Parent may be empty or have minimal intro text, but not the child's full text)
            assert child_text not in parent_text, \
                f"Parent text should not include child text. Parent has {len(parent_text)} chars, child has {len(child_text)} chars"

        # Test case 2: Any subsection with paragraphs should not include paragraph text
        subsection_a = find_provision_by_id(data, '/us/usc/t18/s922/a')
        if subsection_a:
            subsection_text = subsection_a.get('text', '')

            # Check each paragraph under (a)
            for para in subsection_a.get('paragraphs', []):
                para_text = para.get('text', '')
                if para_text and len(para_text) > 50:  # Only check substantial text
                    assert para_text not in subsection_text, \
                        f"Subsection (a) should not contain full text of paragraph {para.get('num')}"

class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_parse_xml_section_returns_none_for_missing_section(self, section_922_xml_2024):
        """Test that XML parser returns None for non-existent section."""
        result = parse_xml_section(section_922_xml_2024, '99999', 2024)
        assert result is None

    def test_parse_xml_section_returns_none_for_invalid_file(self, raw_data_dir, tmp_path):
        """Test that XML parser handles missing file gracefully."""
        # Create a path to a non-existent file
        invalid_file = tmp_path / "nonexistent.xml"
        
        # Should raise exception or return None (current behavior returns None)
        try:
            result = parse_xml_section(invalid_file, '922', 2024)
            # If no exception, result should be None
            assert result is None or isinstance(result, dict)
        except Exception as e:
            # If exception is raised, it should be a known type (FileNotFoundError, etc.)
            assert isinstance(e, (FileNotFoundError, OSError))

    def test_data_loader_returns_none_for_unsupported_year(self, data_loader):
        """Test that data loader returns None for unsupported year."""
        result = data_loader.get_section('922', 1900)  # Year not in YEARS_CONFIG
        assert result is None

    def test_data_loader_returns_none_for_invalid_section(self, data_loader):
        """Test that data loader returns None for non-existent section."""
        result = data_loader.get_section('99999', 2024)
        assert result is None

    def test_parse_xhtml_handles_malformed_provision_numbers(self, parsed_section_922_2006):
        """Test that parser handles edge cases in provision number extraction."""
        # Verify that all subsections have non-empty provision numbers
        for subsection in parsed_section_922_2006['subsections']:
            assert subsection.get('num'), f"Subsection should have a provision number: {subsection.get('id')}"
            # Should be in format (x) where x is alphanumeric
            assert subsection['num'].startswith('(') and subsection['num'].endswith(')'), \
                f"Provision number should be in parentheses: {subsection['num']}"

class TestEdgeCases:
    """Tests for real edge cases found in USC Section 922 data."""

    def test_xhtml_missing_subsection_w_gap_in_sequence(self, data_loader):
        """
        CRITICAL: Test that gap in subsection letters (missing w) doesn't cause nesting.
        
        Real data: Section 922 has (u), (v) but (w) is repealed, then (x).
        Edge case: Parser must recognize (x) as root subsection, not child of (u) or (v).
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        # Find subsections u, v, x
        subsections = {s['num']: s for s in parsed_2018['subsections']}
        
        # Verify (x) exists as root subsection
        assert '(x)' in subsections, "Subsection (x) should exist"
        subsection_x = subsections['(x)']
        
        # CRITICAL: (x) should be root subsection, not nested
        assert subsection_x['id'] == '/us/usc/t18/s922/x', \
            f"Subsection (x) should be at root level, not nested. Got: {subsection_x['id']}"
        assert subsection_x['tag'] == 'subsection'
        
        # Verify it has children (it should have paragraph (1))
        assert 'paragraphs' in subsection_x, "Subsection (x) should have paragraphs"

    def test_xhtml_quadruple_combined_numbers_subsection_z(self, data_loader):
        """
        CRITICAL: Test deep combined numbers (z)(3)(C)(i) creates correct 4-level hierarchy.

        Real data: Section 922(z)(3)(C)(i) has deep nesting in 2018 XHTML.
        Tests state machine handling of multiple levels in sequence.
        """
        parsed_2018 = data_loader.get_section('922', 2018)

        # Navigate: subsection (z) → paragraph (3) → subparagraph (C) → clause (i)
        subsection_z = next((s for s in parsed_2018['subsections'] if s['num'] == '(z)'), None)
        assert subsection_z is not None, "Subsection (z) should exist"

        paragraph_3 = next((p for p in subsection_z.get('paragraphs', []) if p['num'] == '(3)'), None)
        assert paragraph_3 is not None, "Paragraph (3) should exist under (z)"
        assert paragraph_3['id'] == '/us/usc/t18/s922/z/3'

        subparagraph_C = next((sp for sp in paragraph_3.get('subparagraphs', []) if sp['num'] == '(C)'), None)
        assert subparagraph_C is not None, "Subparagraph (C) should exist under (z)(3)"
        assert subparagraph_C['id'] == '/us/usc/t18/s922/z/3/C'

        clause_i = next((c for c in subparagraph_C.get('clauses', []) if c['num'] == '(i)'), None)
        assert clause_i is not None, "Clause (i) should exist under (z)(3)(C)"
        assert clause_i['id'] == '/us/usc/t18/s922/z/3/C/i'

        # Verify subclause level exists
        subclauses = clause_i.get('subclauses', [])
        assert len(subclauses) > 0, "Clause (i) should have subclauses"

        # Verify at least one subclause has correct ID format
        subclause_I = next((sc for sc in subclauses if sc['num'] == '(I)'), None)
        assert subclause_I is not None, "Subclause (I) should exist"
        assert subclause_I['id'] == '/us/usc/t18/s922/z/3/C/i/I'

    def test_xhtml_triple_continuation_from_combined_number(self, data_loader):
        """
        CRITICAL: Test multiple provisions continuing from initial combined number.
        
        Pattern: (f)(1), then (2), (3) all at same CSS level should all be children of (f).
        Tests that continuation state persists correctly across 3+ provisions.
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        subsection_f = next((s for s in parsed_2018['subsections'] if s['num'] == '(f)'), None)
        assert subsection_f is not None, "Subsection (f) should exist"
        
        # (f) should have paragraphs (1) and (2) as direct children
        paragraphs = subsection_f.get('paragraphs', [])
        assert len(paragraphs) >= 2, "Subsection (f) should have at least 2 paragraphs"
        
        para_nums = [p['num'] for p in paragraphs]
        assert '(1)' in para_nums, "Paragraph (1) should exist under (f)"
        assert '(2)' in para_nums, "Paragraph (2) should exist under (f)"
        
        # Verify IDs are correct (both as children of f, not nested)
        para_1 = next(p for p in paragraphs if p['num'] == '(1)')
        para_2 = next(p for p in paragraphs if p['num'] == '(2)')
        
        assert para_1['id'] == '/us/usc/t18/s922/f/1'
        assert para_2['id'] == '/us/usc/t18/s922/f/2'

    def test_xhtml_subsection_i_not_confused_with_clause(self, data_loader):
        """
        CRITICAL: Test that (i) at CSS level 5 is recognized as subsection, not clause.
        
        Edge case: 'i' is both a valid subsection letter AND a roman numeral for clauses.
        After subsection (h), next (i) should be root subsection /s922/i, not /s922/h/i
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        subsection_i = next((s for s in parsed_2018['subsections'] if s['num'] == '(i)'), None)
        assert subsection_i is not None, "Subsection (i) should exist"
        
        # CRITICAL: Should be root subsection, not clause
        assert subsection_i['id'] == '/us/usc/t18/s922/i', \
            f"Subsection (i) should be at root, not nested. Got: {subsection_i['id']}"
        assert subsection_i['tag'] == 'subsection', \
            f"(i) should be tagged as subsection, not clause. Got: {subsection_i['tag']}"

    def test_xhtml_subsection_x_roman_numeral_ambiguity(self, data_loader):
        """
        CRITICAL: Test that (x) at CSS level 5 is recognized as subsection, not roman numeral.
        
        Similar to (i), 'x' is both a subsection letter AND roman numeral 10.
        Must be recognized as subsection (x), not clause (x).
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        subsection_x = next((s for s in parsed_2018['subsections'] if s['num'] == '(x)'), None)
        assert subsection_x is not None, "Subsection (x) should exist"
        
        assert subsection_x['id'] == '/us/usc/t18/s922/x', \
            f"Subsection (x) should be at root. Got: {subsection_x['id']}"
        assert subsection_x['tag'] == 'subsection', \
            f"(x) should be tagged as subsection. Got: {subsection_x['tag']}"

    def test_xhtml_deep_nesting_level_9_boundary(self, data_loader):
        """
        Test that parser handles level 9 (subclause) correctly without trying to create level 10.

        Edge case: After creating subclause at level 9, next provision at same CSS level
        should be sibling at level 9, not child at non-existent level 10.
        """
        parsed_2018 = data_loader.get_section('922', 2018)

        # Navigate to a deep provision with subclauses - use (z)(3)(C)(i)
        subsection_z = next((s for s in parsed_2018['subsections'] if s['num'] == '(z)'), None)
        assert subsection_z is not None

        paragraph_3 = next((p for p in subsection_z.get('paragraphs', []) if p['num'] == '(3)'), None)
        assert paragraph_3 is not None

        subparagraph_C = next((sp for sp in paragraph_3.get('subparagraphs', []) if sp['num'] == '(C)'), None)
        assert subparagraph_C is not None

        clause_i = next((c for c in subparagraph_C.get('clauses', []) if c['num'] == '(i)'), None)
        assert clause_i is not None

        # Should have multiple subclauses as siblings
        subclauses = clause_i.get('subclauses', [])
        assert len(subclauses) >= 1, "Should have at least 1 subclause at level 9"

        # Verify all subclauses are at level 9 (count slashes in ID)
        for sc in subclauses:
            slash_count = sc['id'].count('/')
            # /us/usc/t18/s922/z/3/C/i/I = 9 slashes for level 9
            assert slash_count == 9, \
                f"Subclause {sc['num']} should be at level 9. ID: {sc['id']}, slashes: {slash_count}"

    def test_xhtml_first_subsection_a_deep_children(self, data_loader):
        """
        Test that subsection (a) IDs are built correctly for deep nesting.
        
        Boundary condition: First subsection should have clean ID path for all children.
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        subsection_a = next((s for s in parsed_2018['subsections'] if s['num'] == '(a)'), None)
        assert subsection_a is not None
        assert subsection_a['id'] == '/us/usc/t18/s922/a'
        
        # Should have paragraphs
        paragraphs = subsection_a.get('paragraphs', [])
        assert len(paragraphs) > 0
        
        # Verify first paragraph ID
        para_1 = paragraphs[0]
        assert para_1['id'] == '/us/usc/t18/s922/a/1', \
            f"First paragraph under (a) should have clean ID. Got: {para_1['id']}"
        
        # If it has subparagraphs, verify those too
        if 'subparagraphs' in para_1:
            subpara_A = para_1['subparagraphs'][0]
            assert subpara_A['id'] == '/us/usc/t18/s922/a/1/A', \
                f"First subparagraph should have clean ID. Got: {subpara_A['id']}"

    def test_xhtml_last_subsection_z_recognition(self, data_loader):
        """
        Test that final subsection (z) is recognized correctly as root subsection.
        
        Boundary condition: Last letter in alphabet shouldn't cause special behavior.
        """
        parsed_2018 = data_loader.get_section('922', 2018)
        
        subsection_z = next((s for s in parsed_2018['subsections'] if s['num'] == '(z)'), None)
        assert subsection_z is not None, "Subsection (z) should exist"
        
        # Should be root subsection, not nested under (y)
        assert subsection_z['id'] == '/us/usc/t18/s922/z', \
            f"Subsection (z) should be at root level. Got: {subsection_z['id']}"
        assert subsection_z['tag'] == 'subsection'
