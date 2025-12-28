"""Tests for graph service (Impact Radius & Change Constellation)."""

import pytest
import sys
from pathlib import Path

# Add backend app to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'app'))

from services.graph import get_impact_radius, get_change_constellation, calculate_change_magnitude


class TestCalculateChangeMagnitude:
    """Test the change magnitude calculation helper."""

    def test_zero_delta_returns_zero(self):
        """Text delta of 0 should return magnitude 0.0."""
        assert calculate_change_magnitude(0) == 0.0

    def test_small_changes_under_100(self):
        """Text deltas under 100 chars should return 0.0-0.3."""
        assert calculate_change_magnitude(0) == 0.0
        assert calculate_change_magnitude(50) == pytest.approx(0.15, rel=0.01)
        assert calculate_change_magnitude(99) == pytest.approx(0.297, rel=0.01)

    def test_medium_changes_100_to_500(self):
        """Text deltas 100-500 chars should return 0.3-0.7."""
        assert calculate_change_magnitude(100) == pytest.approx(0.3, rel=0.01)
        assert calculate_change_magnitude(300) == pytest.approx(0.5, rel=0.01)
        assert calculate_change_magnitude(499) == pytest.approx(0.698, rel=0.01)

    def test_large_changes_over_500(self):
        """Text deltas over 500 chars should return 0.7-1.0."""
        assert calculate_change_magnitude(500) == pytest.approx(0.7, rel=0.01)
        assert calculate_change_magnitude(1000) == pytest.approx(0.85, rel=0.01)

    def test_very_large_changes_capped_at_one(self):
        """Very large text deltas should cap at 1.0."""
        assert calculate_change_magnitude(2000) <= 1.0
        assert calculate_change_magnitude(10000) <= 1.0


class TestGraphService:
    """Test graph service functions for impact radius and change constellation."""

    def test_get_impact_radius_returns_correct_structure(self, neo4j_test_driver):
        """Impact radius should return dict with nodes, edges, and stats."""
        # Test with a known provision
        result = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=2,
            include_hierarchical=True,
            include_references=True,
            include_amendments=False
        )

        # Verify structure
        assert 'central_provision' in result
        assert 'year' in result
        assert 'depth' in result
        assert 'nodes' in result
        assert 'edges' in result
        assert 'stats' in result

        # Verify values
        assert result['central_provision'] == '18/922/a'
        assert result['year'] == 2024
        assert result['depth'] == 2
        assert isinstance(result['nodes'], list)
        assert isinstance(result['edges'], list)
        assert isinstance(result['stats'], dict)
        assert 'total' in result['stats']

    def test_get_impact_radius_respects_depth_parameter(self, neo4j_test_driver):
        """Impact radius should limit traversal to specified depth."""
        # Depth 1 should return fewer or equal nodes than depth 2
        result_depth_1 = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=1,
            include_hierarchical=True,
            include_references=False,
            include_amendments=False
        )

        result_depth_2 = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=2,
            include_hierarchical=True,
            include_references=False,
            include_amendments=False
        )

        # Deeper traversal should find more or equal nodes
        assert len(result_depth_2['nodes']) >= len(result_depth_1['nodes'])

        # All nodes in depth 1 should have distance <= 1
        for node in result_depth_1['nodes']:
            assert node['distance'] <= 1

        # Depth 2 can have distance up to 2
        max_distance_2 = max(node['distance'] for node in result_depth_2['nodes']) if result_depth_2['nodes'] else 0
        assert max_distance_2 <= 2

    def test_get_impact_radius_filters_by_relationship_type(self, neo4j_test_driver):
        """Impact radius should respect relationship type filters."""
        # Test with only hierarchical relationships
        result_hierarchical = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=2,
            include_hierarchical=True,
            include_references=False,
            include_amendments=False
        )

        # Test with all relationship types
        result_all = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=2,
            include_hierarchical=True,
            include_references=True,
            include_amendments=True
        )

        # Including more relationship types should find more or equal nodes
        assert len(result_all['nodes']) >= len(result_hierarchical['nodes'])

    def test_get_impact_radius_handles_missing_provision(self, neo4j_test_driver):
        """Impact radius should handle non-existent provisions gracefully."""
        result = get_impact_radius(
            provision_id='99/999/z/99',  # Non-existent provision
            year=2024,
            depth=2,
            include_hierarchical=True,
            include_references=True,
            include_amendments=False
        )

        # Should return empty or minimal result
        assert isinstance(result, dict)
        assert isinstance(result['nodes'], list)
        assert isinstance(result['edges'], list)

    def test_get_impact_radius_nodes_have_required_fields(self, neo4j_test_driver):
        """Impact radius nodes should have all required fields."""
        result = get_impact_radius(
            provision_id='18/922/a',
            year=2024,
            depth=1,
            include_hierarchical=True,
            include_references=False,
            include_amendments=False
        )

        if result['nodes']:
            node = result['nodes'][0]
            assert 'id' in node
            assert 'label' in node
            assert 'distance' in node
            assert 'change_type' in node
            assert 'magnitude' in node
            assert 'text_delta' in node

            # Verify types
            assert isinstance(node['id'], str)
            assert isinstance(node['distance'], int)
            assert isinstance(node['change_type'], str)
            assert isinstance(node['magnitude'], (int, float))
            assert 0.0 <= node['magnitude'] <= 1.0

    def test_get_change_constellation_returns_correct_structure(self, neo4j_test_driver):
        """Change constellation should return dict with nodes, edges, clusters, and year_range."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2020,
            year_end=2024,
            change_types=['modified'],
            min_magnitude=0.0
        )

        # Verify structure
        assert 'year_range' in result
        assert 'nodes' in result
        assert 'edges' in result
        assert 'clusters' in result

        # Verify values
        assert result['year_range'] == (2020, 2024)
        assert isinstance(result['nodes'], list)
        assert isinstance(result['edges'], list)
        assert isinstance(result['clusters'], list)

    def test_get_change_constellation_filters_by_year_range(self, neo4j_test_driver):
        """Change constellation should only return changes in specified year range."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2022,
            year_end=2024,
            change_types=None,
            min_magnitude=0.0
        )

        # All nodes should have years within range
        for node in result['nodes']:
            assert 2022 <= node['year'] <= 2024

    def test_get_change_constellation_filters_by_change_types(self, neo4j_test_driver):
        """Change constellation should filter by specified change types."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2020,
            year_end=2024,
            change_types=['added', 'modified'],  # Exclude 'removed'
            min_magnitude=0.0
        )

        # All nodes should have allowed change types
        for node in result['nodes']:
            assert node['change_type'] in ['added', 'modified']

    def test_get_change_constellation_respects_magnitude_threshold(self, neo4j_test_driver):
        """Change constellation should filter by minimum magnitude."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2020,
            year_end=2024,
            change_types=None,
            min_magnitude=0.5  # Only significant changes
        )

        # All nodes should have magnitude >= 0.5
        for node in result['nodes']:
            assert node['magnitude'] >= 0.5

    def test_get_change_constellation_creates_clusters(self, neo4j_test_driver):
        """Change constellation should group provisions into clusters."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2020,
            year_end=2024,
            change_types=None,
            min_magnitude=0.0
        )

        # If there are nodes, there should be clusters
        if result['nodes']:
            assert len(result['clusters']) > 0

            # Each cluster should have required fields
            for cluster in result['clusters']:
                assert 'cluster_id' in cluster
                assert 'year' in cluster
                assert 'parent_id' in cluster
                assert 'provisions' in cluster
                assert 'count' in cluster

                # Verify cluster has provisions
                assert cluster['count'] > 0
                assert len(cluster['provisions']) == cluster['count']

    def test_get_change_constellation_nodes_have_required_fields(self, neo4j_test_driver):
        """Change constellation nodes should have all required fields."""
        result = get_change_constellation(
            provision_id=None,
            section_num='18/922',
            year_start=2020,
            year_end=2024,
            change_types=None,
            min_magnitude=0.0
        )

        if result['nodes']:
            node = result['nodes'][0]
            assert 'id' in node
            assert 'label' in node
            assert 'year' in node
            assert 'change_type' in node
            assert 'magnitude' in node

            # Verify types
            assert isinstance(node['id'], str)
            assert isinstance(node['year'], int)
            assert isinstance(node['change_type'], str)
            assert isinstance(node['magnitude'], (int, float))
            assert 0.0 <= node['magnitude'] <= 1.0


class TestGraphEndpoints:
    """Test API endpoints for graph visualizations."""

    def test_impact_radius_endpoint_returns_200(self, fastapi_client):
        """Impact radius endpoint should return 200 with valid parameters."""
        response = fastapi_client.get(
            '/provisions/impact-radius/18%2F922%2Fa?year=2024&depth=2'
        )
        assert response.status_code == 200

        data = response.json()
        assert 'central_provision' in data
        assert 'nodes' in data
        assert 'edges' in data
        assert 'stats' in data

    def test_impact_radius_endpoint_validates_parameters(self, fastapi_client):
        """Impact radius endpoint should validate query parameters."""
        # Missing year parameter should use default or return error
        response = fastapi_client.get('/provisions/impact-radius/18%2F922%2Fa')
        # Should either succeed with defaults or return 422 validation error
        assert response.status_code in [200, 422]

    def test_impact_radius_endpoint_handles_filters(self, fastapi_client):
        """Impact radius endpoint should accept relationship filters."""
        response = fastapi_client.get(
            '/provisions/impact-radius/18%2F922%2Fa'
            '?year=2024&depth=2&include_hierarchical=true&include_references=false'
        )
        assert response.status_code == 200

    def test_change_constellation_endpoint_returns_200(self, fastapi_client):
        """Change constellation endpoint should return 200 with valid parameters."""
        response = fastapi_client.get(
            '/provisions/change-constellation?year_start=2020&year_end=2024'
        )
        assert response.status_code == 200

        data = response.json()
        assert 'year_range' in data
        assert 'nodes' in data
        assert 'edges' in data
        assert 'clusters' in data

    def test_change_constellation_endpoint_accepts_filters(self, fastapi_client):
        """Change constellation endpoint should accept optional filters."""
        response = fastapi_client.get(
            '/provisions/change-constellation'
            '?section_num=18/922&year_start=2020&year_end=2024&min_magnitude=0.5'
        )
        assert response.status_code == 200

    def test_change_constellation_endpoint_handles_change_types(self, fastapi_client):
        """Change constellation endpoint should accept change_types filter."""
        response = fastapi_client.get(
            '/provisions/change-constellation'
            '?year_start=2020&year_end=2024&change_types=added&change_types=modified'
        )
        assert response.status_code == 200
