"""Integration tests - End-to-end workflows for parsing and comparison."""

import pytest
from services.diff_engine import compare_versions, get_diff_stats


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_parse_and_compare_workflow(self, data_loader):
        """Test complete workflow: load, parse, and compare two versions."""
        # Load two versions
        version_2024 = data_loader.get_section('922', 2024)
        version_2022 = data_loader.get_section('922', 2022)

        assert version_2024 is not None
        assert version_2022 is not None

        # Compare versions
        diffs = compare_versions(version_2024, version_2022)

        # Get statistics
        stats = get_diff_stats(diffs)

        # Should have meaningful stats
        assert stats['total'] > 0
        assert stats['added'] + stats['deleted'] + stats['modified'] + stats['unchanged'] == stats['total']

    def test_xml_and_xhtml_produce_compatible_structures(self, data_loader):
        """
        Test that XML-parsed and XHTML-parsed sections can be compared.

        This tests that both parsers produce compatible output structures.
        """
        # Load XML version (2024)
        xml_version = data_loader.get_section('922', 2024)

        # Load XHTML version (2006)
        xhtml_version = data_loader.get_section('922', 2006)

        assert xml_version is not None
        assert xhtml_version is not None

        # Should be able to compare without errors
        diffs = compare_versions(xml_version, xhtml_version)

        # Should produce meaningful diffs
        assert len(diffs) > 0

        # Check that diff stats are reasonable
        stats = get_diff_stats(diffs)
        assert stats['total'] == len(diffs)

    def test_compare_section_to_itself_shows_all_unchanged(self, data_loader):
        """Test that comparing a section to itself shows all provisions unchanged."""
        version = data_loader.get_section('922', 2024)

        # Compare to itself
        diffs = compare_versions(version, version)
        stats = get_diff_stats(diffs)

        # All should be unchanged
        assert stats['unchanged'] == stats['total']
        assert stats['added'] == 0
        assert stats['deleted'] == 0
        assert stats['modified'] == 0

    def test_multiple_year_comparisons(self, data_loader):
        """Test comparing section 922 across multiple years."""
        years = [2024, 2022, 2018, 2006]
        versions = {}

        # Load all versions
        for year in years:
            version = data_loader.get_section('922', year)
            if version:
                versions[year] = version

        assert len(versions) >= 3, "Expected at least 3 versions to be available"

        # Compare consecutive years
        year_pairs = list(zip(sorted(versions.keys()), sorted(versions.keys())[1:]))

        for old_year, new_year in year_pairs:
            diffs = compare_versions(versions[old_year], versions[new_year])
            stats = get_diff_stats(diffs)

            # Should have some diffs (laws change over time)
            assert stats['total'] > 0, f"Expected diffs between {old_year} and {new_year}"

    def test_section_structure_consistency_across_formats(self, data_loader):
        """Test that XML and XHTML produce consistent section structures."""
        xml_version = data_loader.get_section('922', 2024)  # XML
        xhtml_version = data_loader.get_section('922', 2018)  # XHTML

        # Both should have same top-level structure
        assert 'id' in xml_version and 'id' in xhtml_version
        assert 'tag' in xml_version and 'tag' in xhtml_version
        assert 'num' in xml_version and 'num' in xhtml_version
        assert 'subsections' in xml_version and 'subsections' in xhtml_version
        assert 'metadata' in xml_version and 'metadata' in xhtml_version

        # Metadata should indicate format
        assert xml_version['metadata']['format'] == 'xml'
        assert xhtml_version['metadata']['format'] == 'xhtml'

    def test_physical_force_provisions_not_falsely_flagged_as_deleted_added(self, data_loader):
        """Test that identical provisions don't show as deleted+added when subsections move."""
        data_2018 = data_loader.get_section('922', 2018)
        data_2024 = data_loader.get_section('922', 2024)

        diffs = compare_versions(data_2018, data_2024)

        # Find diffs for provisions containing "physical force"
        pf_diffs = [d for d in diffs if
                    (d.get('old') and 'physical force' in d.get('old', {}).get('text', '').lower()) or
                    (d.get('new') and 'physical force' in d.get('new', {}).get('text', '').lower())]

        # Check (d)(8)(B)(ii) - should be modified or unchanged, NOT deleted+added
        d8_diffs = [d for d in pf_diffs if '/us/usc/t18/s922/d/8/B/ii' in d.get('id', '')]

        # Should have exactly 1 diff for this provision
        assert len(d8_diffs) == 1, f"Expected 1 diff for (d)(8)(B)(ii), got {len(d8_diffs)}"

        # Should be modified or unchanged, NOT deleted or added
        assert d8_diffs[0]['type'] in ['modified', 'unchanged'], \
            f"(d)(8)(B)(ii) should be modified/unchanged, not {d8_diffs[0]['type']}"
