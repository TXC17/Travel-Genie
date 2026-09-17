"""
Unit and Integration Tests for Spatial K-Means Day-Partitioning Clustering.
Validates Equirectangular projection, adaptive K guardrails, determinism,
spatial dispersion metrics, and REST API behavior.
"""

import pytest
from fastapi import status
from app.algorithms.clustering import SpatialDayClusterer
from app.models.attraction import Attraction
from app.schemas.clustering import ClusteringPartitionRequest
from app.utils.seed import seed_database


def create_mock_attractions():
    """Create 6 test attractions with known geographic coordinates in Hampi region."""
    return [
        Attraction(
            id="hampi_virupaksha",
            destination_id="hampi",
            category="heritage",
            name="Virupaksha Temple",
            description="Sacred temple",
            latitude=15.3350,
            longitude=76.4600,
            average_visit_duration=1.5,
            entry_fee=0.0,
            popularity_score=0.99,
            rating=4.8,
            duration_estimation_method="curated_empirical_average",
        ),
        Attraction(
            id="hampi_hemakuta",
            destination_id="hampi",
            category="heritage",
            name="Hemakuta Hill",
            description="Sunset point adjacent to Virupaksha",
            latitude=15.3330,
            longitude=76.4590,
            average_visit_duration=1.0,
            entry_fee=0.0,
            popularity_score=0.92,
            rating=4.7,
            duration_estimation_method="curated_empirical_average",
        ),
        Attraction(
            id="hampi_vittala",
            destination_id="hampi",
            category="heritage",
            name="Vijaya Vittala Temple",
            description="Stone Chariot complex",
            latitude=15.3400,
            longitude=76.4800,
            average_visit_duration=2.0,
            entry_fee=40.0,
            popularity_score=0.99,
            rating=4.9,
            duration_estimation_method="curated_empirical_average",
        ),
        Attraction(
            id="hampi_lotus_mahal",
            destination_id="hampi",
            category="heritage",
            name="Lotus Mahal Zenana Enclosure",
            description="Royal center",
            latitude=15.3200,
            longitude=76.4700,
            average_visit_duration=1.5,
            entry_fee=40.0,
            popularity_score=0.94,
            rating=4.6,
            duration_estimation_method="curated_empirical_average",
        ),
        Attraction(
            id="hampi_queens_bath",
            destination_id="hampi",
            category="heritage",
            name="Queen's Bath",
            description="Royal bathing pavilion",
            latitude=15.3180,
            longitude=76.4720,
            average_visit_duration=0.75,
            entry_fee=0.0,
            popularity_score=0.88,
            rating=4.4,
            duration_estimation_method="curated_empirical_average",
        ),
        Attraction(
            id="hampi_sanapur",
            destination_id="hampi",
            category="nature",
            name="Sanapur Lake (Across River)",
            description="Scenic reservoir",
            latitude=15.3600,
            longitude=76.4400,
            average_visit_duration=2.0,
            entry_fee=0.0,
            popularity_score=0.91,
            rating=4.6,
            duration_estimation_method="curated_empirical_average",
        ),
    ]


def test_normal_kmeans_partitioning():
    """Test standard spatial clustering when N > K."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()  # N = 6

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=attractions,
        requested_k=2,
    )

    assert res.requested_k == 2
    assert res.effective_k == 2
    assert res.is_k_adjusted is False
    assert res.total_attractions == 6
    assert len(res.clusters) == 2
    assert res.total_inertia_km2 > 0.0

    # Ensure all 6 attractions are partitioned with no drops
    assigned_ids = []
    for day in res.clusters:
        assert day.attraction_count > 0
        assert day.avg_distance_to_centroid_km >= 0.0
        for a in day.attractions:
            assigned_ids.append(a.id)

    assert len(assigned_ids) == 6
    assert set(assigned_ids) == {a.id for a in attractions}


def test_adaptive_k_when_n_less_than_k():
    """Test adaptive guardrail when requested days (K) exceed eligible attractions (N)."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()[:2]  # N = 2

    # Request 4 days for only 2 attractions
    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=attractions,
        requested_k=4,
    )

    assert res.requested_k == 4
    assert res.effective_k == 2  # Adjusted down to N=2
    assert res.is_k_adjusted is True
    assert "exceeds" in res.k_adjustment_reason
    assert len(res.clusters) == 2
    for day in res.clusters:
        assert day.attraction_count == 1


def test_kmeans_when_n_equals_k():
    """Test boundary condition where N == K."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()[:3]  # N = 3

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=attractions,
        requested_k=3,
    )

    assert res.requested_k == 3
    assert res.effective_k == 3
    assert res.is_k_adjusted is False
    assert len(res.clusters) == 3
    for day in res.clusters:
        assert day.attraction_count == 1


def test_empty_candidate_attractions():
    """Test resilience when attraction candidate list is completely empty."""
    clusterer = SpatialDayClusterer()

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=[],
        requested_k=3,
    )

    assert res.effective_k == 0
    assert res.is_k_adjusted is True
    assert res.total_attractions == 0
    assert len(res.clusters) == 0


def test_invalid_coordinates_filtering():
    """Test filtering and explicit exclusion of invalid WGS84 coordinates."""
    clusterer = SpatialDayClusterer()
    valid_attr = create_mock_attractions()[0]
    invalid_attr_out_of_bounds = Attraction(
        id="bad_coords_1",
        destination_id="hampi",
        category="heritage",
        name="Bad Bounds",
        description="Invalid",
        latitude=120.5,  # Invalid latitude > 90
        longitude=76.4,
        average_visit_duration=1.0,
        entry_fee=0.0,
        popularity_score=0.5,
        rating=4.0,
        duration_estimation_method="curated_empirical_average",
    )
    invalid_attr_null_island = Attraction(
        id="bad_coords_2",
        destination_id="hampi",
        category="heritage",
        name="Null Island",
        description="Invalid",
        latitude=0.0,
        longitude=0.0,
        average_visit_duration=1.0,
        entry_fee=0.0,
        popularity_score=0.5,
        rating=4.0,
        duration_estimation_method="curated_empirical_average",
    )

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=[valid_attr, invalid_attr_out_of_bounds, invalid_attr_null_island],
        requested_k=2,
    )

    assert res.total_attractions == 1
    assert len(res.excluded_attractions) == 2
    excluded_ids = [e.attraction_id for e in res.excluded_attractions]
    assert "bad_coords_1" in excluded_ids
    assert "bad_coords_2" in excluded_ids


def test_duplicate_coordinates_handling():
    """Test clustering when two different attractions share the exact same coordinates."""
    clusterer = SpatialDayClusterer()
    attr1 = create_mock_attractions()[0]
    attr2_dup = Attraction(
        id="dup_attraction",
        destination_id="hampi",
        category="heritage",
        name="Virupaksha Complex Inner Shrine",
        description="Inside same compound",
        latitude=attr1.latitude,
        longitude=attr1.longitude,
        average_visit_duration=1.0,
        entry_fee=0.0,
        popularity_score=0.8,
        rating=4.5,
        duration_estimation_method="curated_empirical_average",
    )

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=[attr1, attr2_dup],
        requested_k=1,
    )

    assert res.total_attractions == 2
    assert len(res.clusters) == 1
    assert res.clusters[0].attraction_count == 2


def test_deterministic_clustering_reproducibility():
    """Verify that multiple runs with identical input produce bit-for-bit identical clusters."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()

    res1 = clusterer.partition_days(
        destination_id="hampi", attractions=attractions, requested_k=3
    )
    res2 = clusterer.partition_days(
        destination_id="hampi", attractions=attractions, requested_k=3
    )

    assert res1.effective_k == res2.effective_k
    assert res1.total_inertia_km2 == res2.total_inertia_km2

    for d1, d2 in zip(res1.clusters, res2.clusters):
        assert d1.day_number == d2.day_number
        assert d1.centroid.latitude == d2.centroid.latitude
        assert d1.centroid.longitude == d2.centroid.longitude
        assert [a.id for a in d1.attractions] == [a.id for a in d2.attractions]


def test_geographic_coherence_spatial_dispersion():
    """Verify that geographically adjacent attractions are clustered together."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()  # Virupaksha & Hemakuta are ~200m apart, Lotus Mahal & Queen's Bath are ~300m apart

    res = clusterer.partition_days(
        destination_id="hampi",
        attractions=attractions,
        requested_k=2,
    )

    # Find the cluster containing Virupaksha
    virupaksha_cluster = next(c for c in res.clusters if any(a.id == "hampi_virupaksha" for a in c.attractions))
    virupaksha_cluster_ids = [a.id for a in virupaksha_cluster.attractions]

    # Hemakuta Hill (200m away) must be in the same cluster as Virupaksha
    assert "hampi_hemakuta" in virupaksha_cluster_ids


def test_attraction_assignment_completeness_and_uniqueness():
    """Verify that every single valid attraction is assigned to exactly one day cluster."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()  # 6 attractions

    res = clusterer.partition_days("hampi", attractions, requested_k=3)

    assigned_attractions = []
    for day in res.clusters:
        for attr in day.attractions:
            assigned_attractions.append(attr.id)

    # 1. Total assigned count equals valid input count
    assert len(assigned_attractions) == len(attractions)
    # 2. No duplicate assignments across days
    assert len(set(assigned_attractions)) == len(attractions)
    # 3. Exact matching set
    assert set(assigned_attractions) == {a.id for a in attractions}


def test_day_ordering_by_latitude_north_to_south():
    """Verify that Day 1..K are ordered deterministically by centroid latitude from North to South."""
    clusterer = SpatialDayClusterer()
    attractions = create_mock_attractions()

    res = clusterer.partition_days("hampi", attractions, requested_k=3)

    centroid_latitudes = [day.centroid.latitude for day in res.clusters]
    # Centroid latitudes must be in descending order (North to South)
    assert centroid_latitudes == sorted(centroid_latitudes, reverse=True)


def test_spatially_valid_cluster_time_infeasibility_separation():
    """
    Verify that K-Means clusters purely by geographic proximity and preserves all attractions,
    even if the cluster's aggregate visit duration exceeds daily available sightseeing hours.
    Demonstrates that time-window and duration feasibility is explicitly deferred to Phase 6.
    """
    clusterer = SpatialDayClusterer()
    # 5 attractions closely packed in Hampi, each requiring 2.5 hours of visit duration (Total = 12.5 hours)
    dense_long_attractions = [
        Attraction(
            id=f"dense_attr_{i}",
            destination_id="hampi",
            category="heritage",
            name=f"Expansive Monument {i}",
            description="Large temple complex",
            latitude=15.3300 + (i * 0.001),  # ~100m apart
            longitude=76.4600 + (i * 0.001),
            average_visit_duration=2.5,  # 2.5h each
            entry_fee=40.0,
            popularity_score=0.90,
            rating=4.5,
            duration_estimation_method="curated_empirical_average",
        )
        for i in range(5)
    ]

    # Cluster into 1 day
    res = clusterer.partition_days("hampi", dense_long_attractions, requested_k=1)

    assert len(res.clusters) == 1
    day1 = res.clusters[0]
    # Spatial clustering preserves all 5 geographically close attractions
    assert day1.attraction_count == 5
    assert day1.dispersion_km < 1.0  # Very tight geographic cluster (< 1 km)

    # Calculate total sightseeing time: 5 * 2.5 = 12.5 hours
    total_sightseeing_hours = sum(a.average_visit_duration for a in day1.attractions)
    assert total_sightseeing_hours == 12.5

    # Under standard 8.0h daily limit, this cluster is time-infeasible.
    # K-Means outputs the spatial grouping; Phase 6 OR-Tools & constraint validator handles the pruning.
    assert total_sightseeing_hours > 8.0


def test_clustering_api_endpoint(client, db_session):
    """Test the POST /api/v1/clustering/partition REST endpoint."""
    seed_database(db_session)

    payload = {
        "destination_id": "hampi",
        "requested_k": 3,
        "max_attractions_to_cluster": 10,
    }

    response = client.post("/api/v1/clustering/partition", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["destination_id"] == "hampi"
    assert data["requested_k"] == 3
    assert data["effective_k"] == 3
    assert data["total_attractions"] == 10
    assert len(data["clusters"]) == 3

    for day in data["clusters"]:
        assert day["day_number"] in [1, 2, 3]
        assert day["attraction_count"] > 0
        assert "centroid" in day
        assert "latitude" in day["centroid"]
        assert "longitude" in day["centroid"]
        assert "dispersion_km" in day
        assert "is_low_utilization" in day
        assert len(day["attractions"]) == day["attraction_count"]
