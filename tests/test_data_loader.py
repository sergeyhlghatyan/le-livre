"""Tests for data_loader.py - SectionDataLoader class."""

import pytest
from services.data_loader import SectionDataLoader


class TestDataLoader:
    """Tests for SectionDataLoader class."""

    def test_data_loader_initializes(self, data_dir):
        """Test that SectionDataLoader initializes successfully."""
        loader = SectionDataLoader(data_dir)

        assert loader.data_dir == data_dir
        assert loader.raw_dir == data_dir / 'raw' / 'uslm'

    def test_data_loader_builds_section_index(self, data_loader):
        """Test that SectionDataLoader builds section index on init."""
        # Should have section index for each year
        assert hasattr(data_loader, '_section_index')
        assert len(data_loader._section_index) > 0

        # Should contain 2024
        assert 2024 in data_loader._section_index

        # Section 922 should be in 2024 index
        assert '922' in data_loader._section_index[2024]

    def test_get_section_returns_data(self, data_loader):
        """Test that get_section returns parsed section data."""
        result = data_loader.get_section('922', 2024)

        assert result is not None
        assert result['id'] == '/us/usc/t18/s922'
        assert result['tag'] == 'section'

    def test_get_section_returns_cached_result(self, data_loader):
        """Test that get_section caches parsed results."""
        # First call
        result1 = data_loader.get_section('922', 2024)

        # Second call (should be cached)
        result2 = data_loader.get_section('922', 2024)

        # Should be the same object (from cache)
        assert result1 is result2

    def test_get_section_returns_none_for_invalid_section(self, data_loader):
        """Test that get_section returns None for non-existent section."""
        result = data_loader.get_section('99999', 2024)
        assert result is None

    def test_get_section_returns_none_for_invalid_year(self, data_loader):
        """Test that get_section returns None for unsupported year."""
        result = data_loader.get_section('922', 1800)
        assert result is None

    def test_get_section_versions_returns_all_versions(self, data_loader):
        """Test that get_section_versions returns all available versions."""
        versions = data_loader.get_section_versions('922')

        # Should have multiple versions
        assert len(versions) >= 4  # At least 2024, 2022, 2018, 2006

        # Should include expected years
        assert 2024 in versions
        assert 2022 in versions
        assert 2006 in versions

        # Each version should be parsed data
        assert versions[2024]['id'] == '/us/usc/t18/s922'

    def test_get_available_years_returns_sorted_years(self, data_loader):
        """Test that get_available_years returns sorted list."""
        years = data_loader.get_available_years()

        assert isinstance(years, list)
        assert len(years) > 0
        assert years == sorted(years, reverse=True)  # Descending order
        assert 2024 in years

    def test_clear_cache_clears_cached_sections(self, data_loader):
        """Test that clear_cache removes cached parsed data."""
        # Load a section
        data_loader.get_section('922', 2024)

        # Cache should have entry
        assert len(data_loader._cache) > 0

        # Clear cache
        data_loader.clear_cache()

        # Cache should be empty
        assert len(data_loader._cache) == 0
