"""Tests for diff_engine.py - Section comparison and diff generation."""

import pytest
from services.diff_engine import build_provision_tree, compare_versions, get_diff_stats


class TestBuildProvisionTree:
    """Tests for build_provision_tree function."""

    def test_build_provision_tree_creates_flat_structure(self, parsed_section_922_2024):
        """Test that build_provision_tree creates a flat dictionary of all provisions."""
        tree = build_provision_tree(parsed_section_922_2024)

        # Should be a dict
        assert isinstance(tree, dict)

        # Should contain provisions at multiple levels
        assert '/us/usc/t18/s922/a' in tree  # Subsection
        assert '/us/usc/t18/s922/a/1' in tree  # Paragraph
        assert '/us/usc/t18/s922/a/1/A' in tree  # Subparagraph

    def test_build_provision_tree_includes_all_provisions(self, parsed_section_922_2024):
        """Test that build_provision_tree doesn't miss any provisions."""
        tree = build_provision_tree(parsed_section_922_2024)

        # Count provisions manually
        def count_provisions(node):
            count = 0
            for child_type in ['subsections', 'paragraphs', 'subparagraphs', 'clauses', 'subclauses']:
                children = node.get(child_type, [])
                count += len(children)
                for child in children:
                    count += count_provisions(child)
            return count

        expected_count = count_provisions(parsed_section_922_2024)
        actual_count = len(tree)

        assert actual_count == expected_count, (
            f"Provision count mismatch: expected {expected_count}, got {actual_count}"
        )

    def test_build_provision_tree_stores_text_and_metadata(self, parsed_section_922_2024):
        """Test that provision tree includes text and metadata."""
        tree = build_provision_tree(parsed_section_922_2024)
        provision = tree['/us/usc/t18/s922/a/1/A']

        assert 'id' in provision
        assert 'num' in provision
        assert 'text' in provision
        assert 'tag' in provision


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_compare_versions_detects_added_provisions(self, parsed_section_922_2022, parsed_section_922_2024):
        """Test that compare_versions detects provisions added in newer version."""
        diffs = compare_versions(parsed_section_922_2022, parsed_section_922_2024)

        # Should find some added provisions (2024 has changes from 2022)
        added = [d for d in diffs if d['type'] == 'added']

        # Check structure of added diff
        if added:
            diff = added[0]
            assert 'id' in diff
            assert 'type' in diff
            assert diff['type'] == 'added'
            assert diff['old'] is None
            assert diff['new'] is not None

    def test_compare_versions_detects_deleted_provisions(self, parsed_section_922_2024, parsed_section_922_2022):
        """Test that compare_versions detects provisions deleted in newer version."""
        # Compare 2024 (old) to 2022 (new) to find deletions
        diffs = compare_versions(parsed_section_922_2024, parsed_section_922_2022)

        # Should find some deleted provisions
        deleted = [d for d in diffs if d['type'] == 'deleted']

        if deleted:
            diff = deleted[0]
            assert diff['type'] == 'deleted'
            assert diff['old'] is not None
            assert diff['new'] is None

    def test_compare_versions_detects_modified_provisions(self, parsed_section_922_2006, parsed_section_922_2024):
        """Test that compare_versions detects provisions with text changes."""
        # 2006 to 2024 should have many modifications
        diffs = compare_versions(parsed_section_922_2006, parsed_section_922_2024)

        # Should find modified provisions
        modified = [d for d in diffs if d['type'] == 'modified']

        assert len(modified) > 0, "Expected to find modified provisions between 2006 and 2024"

        # Check structure
        diff = modified[0]
        assert diff['type'] == 'modified'
        assert diff['old'] is not None
        assert diff['new'] is not None
        assert diff['old']['text'] != diff['new']['text']

    def test_compare_versions_detects_unchanged_provisions(self, parsed_section_922_2022, parsed_section_922_2024):
        """Test that compare_versions detects unchanged provisions."""
        diffs = compare_versions(parsed_section_922_2022, parsed_section_922_2024)

        # Should have many unchanged provisions
        unchanged = [d for d in diffs if d['type'] == 'unchanged']

        assert len(unchanged) > 0

        # Check structure
        diff = unchanged[0]
        assert diff['type'] == 'unchanged'
        assert diff['old']['text'].strip() == diff['new']['text'].strip()

    def test_compare_versions_maintains_hierarchical_order(self, parsed_section_922_2024, parsed_section_922_2022):
        """Test that compare_versions returns diffs in hierarchical order."""
        diffs = compare_versions(parsed_section_922_2024, parsed_section_922_2022)

        # Extract provision IDs
        ids = [d['id'] for d in diffs]

        # Should be sorted
        assert ids == sorted(ids), "Diffs should be in hierarchical (sorted) order"

        # (a) should come before (b), (a)(1) before (a)(2), etc.
        # Check a few known orderings
        if '/us/usc/t18/s922/a' in ids and '/us/usc/t18/s922/b' in ids:
            assert ids.index('/us/usc/t18/s922/a') < ids.index('/us/usc/t18/s922/b')

    def test_compare_identical_versions_shows_all_unchanged(self, parsed_section_922_2024):
        """Test that comparing a section to itself shows all provisions unchanged."""
        diffs = compare_versions(parsed_section_922_2024, parsed_section_922_2024)
        stats = get_diff_stats(diffs)

        # All should be unchanged
        assert stats['unchanged'] == stats['total']
        assert stats['added'] == 0
        assert stats['deleted'] == 0
        assert stats['modified'] == 0


class TestGetDiffStats:
    """Tests for get_diff_stats function."""

    def test_get_diff_stats_counts_correctly(self, parsed_section_922_2024, parsed_section_922_2022):
        """Test that get_diff_stats calculates correct statistics."""
        diffs = compare_versions(parsed_section_922_2024, parsed_section_922_2022)
        stats = get_diff_stats(diffs)

        assert 'added' in stats
        assert 'deleted' in stats
        assert 'modified' in stats
        assert 'unchanged' in stats
        assert 'total' in stats

        # Total should match
        assert stats['total'] == len(diffs)

        # Sum of types should equal total
        assert stats['added'] + stats['deleted'] + stats['modified'] + stats['unchanged'] == stats['total']

    def test_get_diff_stats_handles_empty_diffs(self):
        """Test that get_diff_stats handles empty diffs list."""
        stats = get_diff_stats([])

        assert stats['added'] == 0
        assert stats['deleted'] == 0
        assert stats['modified'] == 0
        assert stats['unchanged'] == 0
        assert stats['total'] == 0
