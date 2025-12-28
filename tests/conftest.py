"""Shared pytest fixtures for USC section parsing and comparison tests."""

import pytest
from pathlib import Path
import sys

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))


@pytest.fixture
def data_dir():
    """Path to actual data directory."""
    return Path('/Users/sergeyhlghatyan/dev/ocean/lelivre/data')


@pytest.fixture
def raw_data_dir(data_dir):
    """Path to raw USLM data."""
    return data_dir / 'raw' / 'uslm'


# XML File Path Fixtures
@pytest.fixture
def section_922_xml_2024(raw_data_dir):
    """Path to actual 2024 XML file containing section 922."""
    return raw_data_dir / '2024' / 'usc18.xml'


@pytest.fixture
def section_922_xml_2022(raw_data_dir):
    """Path to actual 2022 XML file containing section 922."""
    return raw_data_dir / '2022' / 'usc18.xml'


# XHTML File Path Fixtures
@pytest.fixture
def section_922_xhtml_2018(raw_data_dir):
    """Path to actual 2018 XHTML file containing section 922."""
    return raw_data_dir / '2018' / '2018' / '2018usc18.htm'


@pytest.fixture
def section_922_xhtml_2006(raw_data_dir):
    """Path to actual 2006 XHTML file containing section 922."""
    return raw_data_dir / '2006' / '2006' / '2006usc18.htm'


# Parsed Section Fixtures (cached for efficiency)
@pytest.fixture
def parsed_section_922_2024(section_922_xml_2024):
    """Parse and return section 922 from 2024 XML."""
    from services.usc_parser import parse_xml_section
    return parse_xml_section(section_922_xml_2024, '922', 2024)


@pytest.fixture
def parsed_section_922_2022(section_922_xml_2022):
    """Parse and return section 922 from 2022 XML."""
    from services.usc_parser import parse_xml_section
    return parse_xml_section(section_922_xml_2022, '922', 2022)


@pytest.fixture
def parsed_section_922_2018(section_922_xhtml_2018):
    """Parse and return section 922 from 2018 XHTML."""
    from services.usc_parser import parse_xhtml_section
    return parse_xhtml_section(section_922_xhtml_2018, '922', 2018)


@pytest.fixture
def parsed_section_922_2006(section_922_xhtml_2006):
    """Parse and return section 922 from 2006 XHTML."""
    from services.usc_parser import parse_xhtml_section
    return parse_xhtml_section(section_922_xhtml_2006, '922', 2006)


# Data Loader Fixture
@pytest.fixture
def data_loader(data_dir):
    """Initialize SectionDataLoader with actual data directory."""
    from services.data_loader import SectionDataLoader
    return SectionDataLoader(data_dir)


# Neo4j Test Fixture (for graph service tests)
@pytest.fixture
def neo4j_test_driver():
    """Provide Neo4j driver for testing graph services."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'app'))

    from database import get_neo4j_driver
    return get_neo4j_driver()


# FastAPI Test Client Fixture (for API endpoint tests)
@pytest.fixture
def fastapi_client():
    """FastAPI test client for testing endpoints."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
