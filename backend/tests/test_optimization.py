"""
Unit and Integration Tests for Google OR-Tools Route Optimization & Constraint Scheduling.
Validates TSP route sequencing, distance reduction metrics, time window compliance,
MCDM priority-based pruning, and end-to-end multi-day trip scheduling.
"""

import pytest
from pydantic import ValidationError
from fastapi import status
from app.algorithms.route_optimizer import IntraDayRouteOptimizer
from app.algorithms.clustering import SpatialDayClusterer
from app.models.attraction import Attraction
from app.schemas.attraction import AttractionResponse
from app.schemas.clustering import ClusterDaySchema, ClusterCentroidSchema
from app.schemas.optimization import (
    DayOptimizationRequest,
    MultiDayTripOptimizationRequest,
    RouteEndpointSchema,
)
from app.utils.seed import seed_database


def create_sample_cluster_attractions():
    """Create 4 attractions located in Hampi with varying coordinates and opening hours."""
    return [
        AttractionResponse(
            id="hampi_virupaksha",
            destination_id="hampi",
            category="heritage",
            name="Virupaksha Temple",
            description="Sacred center",
            latitude=15.3350,
            longitude=76.4600,
            average_visit_duration=1.5,
            entry_fee=0.0,
            popularity_score=0.99,
            rating=4.8,
            opening_time="06:00:00",
            closing_time="20:00:00",
            best_time_to_visit="Morning",
            is_seasonal_closure=False,
            is_verified=True,
            duration_estimation_method="curated_empirical_average",
        ),
        AttractionResponse(
            id="hampi_hemakuta",
            destination_id="hampi",
            category="heritage",
            name="Hemakuta Hill",
            description="Adjacent hill",
            latitude=15.3330,
            longitude=76.4590,
            average_visit_duration=1.0,
            entry_fee=0.0,
            popularity_score=0.92,
            rating=4.7,
            opening_time="06:00:00",
            closing_time="19:00:00",
            best_time_to_visit="Sunset",
            is_seasonal_closure=False,
            is_verified=True,
            duration_estimation_method="curated_empirical_average",
        ),
        AttractionResponse(
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
            opening_time="08:30:00",
            closing_time="17:30:00",
            best_time_to_visit="Morning",
            is_seasonal_closure=False,
            is_verified=True,
            duration_estimation_method="curated_empirical_average",
        ),
        AttractionResponse(
            id="hampi_vittala",
            destination_id="hampi",
            category="heritage",
            name="Vijaya Vittala Temple",
            description="Stone Chariot",
            latitude=15.3400,
            longitude=76.4800,
            average_visit_duration=2.0,
            entry_fee=40.0,
            popularity_score=0.99,
            rating=4.9,
            opening_time="08:30:00",
            closing_time="17:30:00",
            best_time_to_visit="Morning",
            is_seasonal_closure=False,
            is_verified=True,
            duration_estimation_method="curated_empirical_average",
        ),
    ]


def test_single_attraction_route_optimization():
    """Verify single attraction edge case yields 0 km travel distance and 0 reduction."""
    optimizer = IntraDayRouteOptimizer()
    attractions = create_sample_cluster_attractions()[:1]

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=1,
        centroid=ClusterCentroidSchema(latitude=15.335, longitude=76.460),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        is_low_utilization=True,
        attractions=attractions,
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)

    assert schedule.attraction_count == 1
    assert len(deferred) == 0
    assert schedule.total_travel_distance_km == 0.0
    assert schedule.total_travel_duration_hours == 0.0
    assert schedule.optimization_metrics.distance_reduction_pct == 0.0
    assert schedule.items[0].arrival_time == "09:00"
    assert schedule.items[0].departure_time == "10:30"


def test_ortools_tsp_route_improvement_over_zigzag_baseline():
    """Verify OR-Tools optimizes visit sequence and achieves non-negative distance reduction."""
    optimizer = IntraDayRouteOptimizer()
    # Ordered in zigzag fashion: Virupaksha (Northwest), Lotus Mahal (South), Vittala (Northeast), Hemakuta (Northwest)
    attractions = [
        create_sample_cluster_attractions()[0],  # Virupaksha
        create_sample_cluster_attractions()[2],  # Lotus Mahal (South)
        create_sample_cluster_attractions()[3],  # Vittala (Northeast)
        create_sample_cluster_attractions()[1],  # Hemakuta (Northwest)
    ]

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=4,
        centroid=ClusterCentroidSchema(latitude=15.332, longitude=76.467),
        avg_distance_to_centroid_km=1.2,
        max_distance_to_centroid_km=2.0,
        dispersion_km=3.5,
        attractions=attractions,
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Intense",  # 10h limit allows all 4 to fit
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)

    assert schedule.attraction_count == 4
    assert len(deferred) == 0
    # Optimized route distance should be less than or equal to unoptimized zigzag distance
    orig_dist = schedule.optimization_metrics.original_route_distance_km
    opt_dist = schedule.optimization_metrics.optimized_route_distance_km
    assert opt_dist <= orig_dist
    assert schedule.optimization_metrics.distance_reduction_km >= 0.0
    assert schedule.optimization_metrics.distance_reduction_pct >= 0.0
    assert len(schedule.legs) == 3  # 3 transit legs between 4 stops


def test_daily_pace_constraint_and_mcdm_priority_pruning():
    """Verify that when total day duration exceeds pace limit, the lowest MCDM stop is pruned."""
    optimizer = IntraDayRouteOptimizer()
    attractions = create_sample_cluster_attractions()  # 4 attractions total 1.5 + 1.0 + 1.5 + 2.0 = 6.0h + transit

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=4,
        centroid=ClusterCentroidSchema(latitude=15.332, longitude=76.467),
        avg_distance_to_centroid_km=1.2,
        max_distance_to_centroid_km=2.0,
        dispersion_km=3.5,
        attractions=attractions,
    )

    # Set custom MCDM scores where Hemakuta is lowest (0.60)
    mcdm_scores = {
        "hampi_virupaksha": 0.95,
        "hampi_vittala": 0.98,
        "hampi_lotus_mahal": 0.88,
        "hampi_hemakuta": 0.60,
    }

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="walking",  # Walking speed 4.5 km/h makes total day duration > 6.0h
        pace="Relaxed",  # Strict 6.0h daily limit
        mcdm_scores_map=mcdm_scores,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)

    # Must prune lowest MCDM attraction (Hemakuta) to fit under 6h limit
    assert len(deferred) > 0
    deferred_ids = [d.attraction_id for d in deferred]
    assert "hampi_hemakuta" in deferred_ids
    assert schedule.total_day_duration_hours <= 6.0
    assert "daily_time_limit" in deferred[0].violating_constraint


def test_opening_hours_and_waiting_time_calculation():
    """Verify arrival at an attraction before opening time results in accurate waiting time."""
    optimizer = IntraDayRouteOptimizer()
    # Create attraction that opens late at 11:00 AM
    late_opening_attr = AttractionResponse(
        id="late_museum",
        destination_id="hampi",
        category="museum",
        name="Archaeological Museum",
        description="Museum",
        latitude=15.3351,
        longitude=76.4601,
        average_visit_duration=1.0,
        entry_fee=20.0,
        popularity_score=0.75,
        rating=4.3,
        opening_time="11:00:00",
        closing_time="17:00:00",
        is_seasonal_closure=False,
        is_verified=True,
    )

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=1,
        centroid=ClusterCentroidSchema(latitude=15.335, longitude=76.460),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        attractions=[late_opening_attr],
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        day_start_time="09:00",
        pace="Moderate",
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)

    assert schedule.attraction_count == 1
    # Arrival is 09:00, but opening is 11:00 -> Waiting time = 2.0 hours
    item = schedule.items[0]
    assert item.arrival_time == "09:00"
    assert item.waiting_time_hours == 2.0
    assert item.departure_time == "12:00"  # 11:00 + 1.0h visit = 12:00


def test_deterministic_reproducibility_of_optimizer():
    """Verify identical inputs produce bit-for-bit identical schedules and metrics."""
    optimizer = IntraDayRouteOptimizer()
    attractions = create_sample_cluster_attractions()

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=4,
        centroid=ClusterCentroidSchema(latitude=15.332, longitude=76.467),
        avg_distance_to_centroid_km=1.2,
        max_distance_to_centroid_km=2.0,
        dispersion_km=3.5,
        attractions=attractions,
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
    )

    res1, _ = optimizer.optimize_day_schedule(req)
    res2, _ = optimizer.optimize_day_schedule(req)

    assert res1.total_travel_distance_km == res2.total_travel_distance_km
    assert res1.total_day_duration_hours == res2.total_day_duration_hours
    assert [i.attraction.id for i in res1.items] == [i.attraction.id for i in res2.items]


def test_transport_mode_cost_and_speed_differences():
    """Verify walking vs auto changes travel duration and estimated cost."""
    optimizer = IntraDayRouteOptimizer()
    attractions = create_sample_cluster_attractions()[:3]

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=3,
        centroid=ClusterCentroidSchema(latitude=15.332, longitude=76.467),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=1.5,
        dispersion_km=2.5,
        attractions=attractions,
    )

    req_auto = DayOptimizationRequest(
        destination_id="hampi", day_number=1, cluster=cluster, preferred_transport="auto", pace="Intense"
    )
    req_taxi = DayOptimizationRequest(
        destination_id="hampi", day_number=1, cluster=cluster, preferred_transport="taxi", pace="Intense"
    )

    res_auto, _ = optimizer.optimize_day_schedule(req_auto)
    res_taxi, _ = optimizer.optimize_day_schedule(req_taxi)

    # Taxi is faster than auto (35 km/h vs 25 km/h) -> lower travel duration
    assert res_taxi.total_travel_duration_hours < res_auto.total_travel_duration_hours
    # Taxi is more expensive than auto
    assert res_taxi.day_estimated_transit_cost > res_auto.day_estimated_transit_cost


def test_already_optimal_baseline_produces_zero_percent_reduction():
    """Verify that if the baseline input order is already optimal, reduction is 0.0% with no false claims."""
    optimizer = IntraDayRouteOptimizer()
    # Ordered linearly in straight line: Virupaksha -> Hemakuta -> Lotus Mahal
    attractions = [
        create_sample_cluster_attractions()[0],  # Virupaksha
        create_sample_cluster_attractions()[1],  # Hemakuta
        create_sample_cluster_attractions()[2],  # Lotus Mahal
    ]

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=3,
        centroid=ClusterCentroidSchema(latitude=15.332, longitude=76.467),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=1.5,
        dispersion_km=2.5,
        attractions=attractions,
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Intense",
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert len(deferred) == 0
    assert schedule.optimization_metrics.distance_reduction_pct >= 0.0
    assert schedule.optimization_metrics.original_route_distance_km == schedule.optimization_metrics.optimized_route_distance_km


def test_zero_distance_and_duplicate_coordinates_edge_case():
    """Verify route optimization when multiple attractions are co-located at identical coordinates."""
    optimizer = IntraDayRouteOptimizer()
    attr1 = create_sample_cluster_attractions()[0]
    attr2_colocated = AttractionResponse(
        id="colocated_temple_shrine",
        destination_id="hampi",
        category="heritage",
        name="Inner Shrine",
        description="Same location",
        latitude=attr1.latitude,
        longitude=attr1.longitude,
        average_visit_duration=1.0,
        entry_fee=0.0,
        popularity_score=0.80,
        rating=4.5,
        opening_time="06:00:00",
        closing_time="20:00:00",
        is_seasonal_closure=False,
        is_verified=True,
    )

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=2,
        centroid=ClusterCentroidSchema(latitude=attr1.latitude, longitude=attr1.longitude),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        attractions=[attr1, attr2_colocated],
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.attraction_count == 2
    assert schedule.total_travel_distance_km == 0.0
    assert schedule.optimization_metrics.distance_reduction_pct == 0.0


def test_extreme_overload_all_attractions_pruned_edge_case():
    """Verify behavior when a single attraction alone exceeds the daily pace limit."""
    optimizer = IntraDayRouteOptimizer()
    mega_trek = AttractionResponse(
        id="mega_trek",
        destination_id="hampi",
        category="adventure",
        name="All-Day Multi-Mountain Wilderness Trek",
        description="Exceeds day limit",
        latitude=15.350,
        longitude=76.450,
        average_visit_duration=12.0,  # 12 hours visit alone
        entry_fee=100.0,
        popularity_score=0.90,
        rating=4.8,
        opening_time="06:00:00",
        closing_time="23:00:00",  # Open until late so it specifically triggers the daily pace limit
        is_seasonal_closure=False,
        is_verified=True,
    )

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=1,
        centroid=ClusterCentroidSchema(latitude=15.350, longitude=76.450),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        attractions=[mega_trek],
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        pace="Relaxed",  # Strict 6h limit < 12h
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.attraction_count == 0
    assert len(deferred) == 1
    assert deferred[0].attraction_id == "mega_trek"
    assert "daily_time_limit" in deferred[0].violating_constraint


def test_attraction_open_duration_shorter_than_visit_duration_pruned():
    """Verify that an attraction open for less time than its visit duration is detected and pruned."""
    optimizer = IntraDayRouteOptimizer()
    short_window_attr = AttractionResponse(
        id="short_window_site",
        destination_id="hampi",
        category="heritage",
        name="Briefly Open Monument",
        description="Only open for 30 minutes",
        latitude=15.335,
        longitude=76.460,
        average_visit_duration=2.0,  # Needs 2 hours
        entry_fee=10.0,
        popularity_score=0.70,
        rating=4.0,
        opening_time="10:00:00",
        closing_time="10:30:00",  # Only open for 30 min (0.5h) < 2.0h
        is_seasonal_closure=False,
        is_verified=True,
    )

    cluster = ClusterDaySchema(
        day_number=1,
        cluster_id=0,
        attraction_count=1,
        centroid=ClusterCentroidSchema(latitude=15.335, longitude=76.460),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        attractions=[short_window_attr],
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        pace="Moderate",
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.attraction_count == 0
    assert len(deferred) == 1
    assert deferred[0].attraction_id == "short_window_site"
    assert deferred[0].violating_constraint == "visit_duration"


def test_end_to_end_phase5_clustering_to_phase6_optimization(client, db_session):
    """
    End-to-end integration test:
    Phase 5 K-Means Spatial Clustering -> Phase 6 OR-Tools Route Optimization.
    """
    seed_database(db_session)

    # 1. Execute Phase 5 Spatial Clustering
    cluster_payload = {
        "destination_id": "hampi",
        "requested_k": 2,
        "max_attractions_to_cluster": 8,
    }
    cluster_res = client.post("/api/v1/clustering/partition", json=cluster_payload)
    assert cluster_res.status_code == status.HTTP_200_OK
    cluster_data = cluster_res.json()
    assert cluster_data["effective_k"] == 2
    assert len(cluster_data["clusters"]) == 2

    # 2. Execute Phase 6 Route Optimization via /route endpoint
    opt_payload = {
        "destination_id": "hampi",
        "clusters": cluster_data["clusters"],
        "preferred_transport": "auto",
        "pace": "Moderate",
        "day_start_time": "09:00",
    }
    opt_res = client.post("/api/v1/optimization/route", json=opt_payload)
    assert opt_res.status_code == status.HTTP_200_OK
    opt_data = opt_res.json()

    assert opt_data["destination_id"] == "hampi"
    assert opt_data["total_days"] == 2
    assert opt_data["total_scheduled_attractions"] > 0
    assert len(opt_data["days"]) == 2

    for day in opt_data["days"]:
        assert day["day_number"] in [1, 2]
        assert "feasibility_status" in day
        assert "route_sequence" in day
        assert "ordered_attractions" in day
        assert "optimization_metrics" in day
        assert "items" in day
        assert "legs" in day
        assert day["total_day_duration_hours"] <= 8.0  # Respects Moderate pace


def test_accommodation_aware_day_optimization_round_trip():
    """
    Test Phase 3: Hotel as daily origin and destination (round trip).
    Verifies that origin and return legs are generated with correct distance and duration.
    """
    optimizer = IntraDayRouteOptimizer()
    attrs = create_sample_cluster_attractions()[:3]
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        attraction_count=len(attrs),
        centroid=ClusterCentroidSchema(latitude=15.33, longitude=76.46),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=2.0,
        dispersion_km=2.0,
        attractions=attrs,
    )

    hotel = RouteEndpointSchema(
        id="acc_hampi_boulders",
        name="Hampi Boulders Resort",
        latitude=15.3600,
        longitude=76.4900,
        endpoint_type="accommodation",
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
        accommodation=hotel,
        return_to_accommodation=True,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.feasibility_status in ["FEASIBLE", "FEASIBLE_AFTER_PRUNING"]
    assert schedule.start_location_type == "accommodation"
    assert schedule.start_location_name == hotel.name
    assert schedule.end_location_type == "accommodation"
    assert schedule.end_location_name == hotel.name
    assert schedule.is_round_trip is True

    # Accommodation legs verification
    assert schedule.accommodation_origin_leg is not None
    assert schedule.accommodation_origin_leg.from_attraction_id == hotel.id
    assert schedule.accommodation_origin_leg.leg_type == "origin_to_first_attraction"
    assert schedule.accommodation_origin_leg.distance_km > 0.0

    assert schedule.accommodation_return_leg is not None
    assert schedule.accommodation_return_leg.to_attraction_id == hotel.id
    assert schedule.accommodation_return_leg.leg_type == "last_attraction_to_destination"
    assert schedule.accommodation_return_leg.distance_km > 0.0

    # Ensure legs include origin leg + intra-attraction legs + return leg
    assert len(schedule.legs) == len(schedule.items) + 1
    assert schedule.total_travel_distance_km >= (
        schedule.accommodation_origin_leg.distance_km + schedule.accommodation_return_leg.distance_km
    )


def test_accommodation_aware_day_optimization_open_ended():
    """
    Test Phase 3: Hotel as daily origin but open-ended (return_to_accommodation=False).
    """
    optimizer = IntraDayRouteOptimizer()
    attrs = create_sample_cluster_attractions()[:3]
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        attraction_count=len(attrs),
        centroid=ClusterCentroidSchema(latitude=15.33, longitude=76.46),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=2.0,
        dispersion_km=2.0,
        attractions=attrs,
    )

    hotel = RouteEndpointSchema(
        id="acc_hampi_boulders",
        name="Hampi Boulders Resort",
        latitude=15.3600,
        longitude=76.4900,
        endpoint_type="accommodation",
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
        accommodation=hotel,
        return_to_accommodation=False,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.start_location_type == "accommodation"
    assert schedule.end_location_type == "attraction"
    assert schedule.is_round_trip is False
    assert schedule.accommodation_origin_leg is not None
    assert schedule.accommodation_return_leg is None
    assert len(schedule.legs) == len(schedule.items)


def test_no_accommodation_fallback_preservation():
    """
    Test that when accommodation is None, behavior preserves the original
    attraction-to-attraction open tour starting at attraction 0.
    """
    optimizer = IntraDayRouteOptimizer()
    attrs = create_sample_cluster_attractions()[:3]
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        attraction_count=len(attrs),
        centroid=ClusterCentroidSchema(latitude=15.33, longitude=76.46),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=2.0,
        dispersion_km=2.0,
        attractions=attrs,
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
        accommodation=None,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert schedule.start_location_type == "attraction"
    assert schedule.end_location_type == "attraction"
    assert schedule.is_round_trip is False
    assert schedule.accommodation_origin_leg is None
    assert schedule.accommodation_return_leg is None
    assert len(schedule.legs) == len(schedule.items) - 1


def test_accommodation_pace_limit_pruning():
    """
    Test that including long hotel travel legs respects daily pace limit and prunes
    attractions via MCDM score when needed.
    """
    optimizer = IntraDayRouteOptimizer()
    attrs = create_sample_cluster_attractions()  # 4 attractions
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        attraction_count=len(attrs),
        centroid=ClusterCentroidSchema(latitude=15.33, longitude=76.46),
        avg_distance_to_centroid_km=1.0,
        max_distance_to_centroid_km=2.0,
        dispersion_km=2.0,
        attractions=attrs,
    )

    # Hotel located far away (50 km away), with Relaxed pace (6.0 hour limit)
    far_hotel = RouteEndpointSchema(
        id="acc_far_away",
        name="Far Resort",
        latitude=15.0000,
        longitude=76.0000,
        endpoint_type="accommodation",
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Relaxed",  # 6 hour limit
        accommodation=far_hotel,
        return_to_accommodation=True,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)
    # Total day duration must respect the 6.0 hour pace limit
    assert schedule.total_day_duration_hours <= 6.0
    # At least some attractions should be pruned to satisfy the pace limit
    assert len(deferred) > 0


def test_accommodation_aware_api_endpoint(client, db_session):
    """
    Test /api/v1/optimization/route endpoint with accommodation endpoint payload.
    """
    seed_database(db_session)

    attrs = create_sample_cluster_attractions()[:3]
    clusters = [
        {
            "cluster_id": 0,
            "day_number": 1,
            "attraction_count": len(attrs),
            "attractions": [a.model_dump() for a in attrs],
            "centroid": {"latitude": 15.33, "longitude": 76.46},
            "avg_distance_to_centroid_km": 1.0,
            "max_distance_to_centroid_km": 2.0,
            "dispersion_km": 2.0,
            "is_low_utilization": False,
        }
    ]

    payload = {
        "destination_id": "hampi",
        "clusters": clusters,
        "preferred_transport": "auto",
        "pace": "Moderate",
        "day_start_time": "09:00",
        "accommodation": {
            "id": "acc_hampi_test",
            "name": "Hampi Heritage Stay",
            "latitude": 15.3300,
            "longitude": 76.4600,
            "endpoint_type": "accommodation",
        },
        "return_to_accommodation": True,
    }

    res = client.post("/api/v1/optimization/route", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["days"]) == 1
    day1 = data["days"][0]
    assert day1["start_location_type"] == "accommodation"
    assert day1["start_location_name"] == "Hampi Heritage Stay"
    assert day1["accommodation_origin_leg"] is not None
    assert day1["accommodation_return_leg"] is not None


def test_route_endpoint_schema_coordinate_validation():
    """
    TASK 1: Verify RouteEndpointSchema rejects coordinates out of bounds:
    - Latitude > 90 or < -90
    - Longitude > 180 or < -180
    """
    # Valid coordinates should succeed
    endpoint = RouteEndpointSchema(
        id="acc_valid",
        name="Valid Hotel",
        latitude=15.33,
        longitude=76.46,
    )
    assert endpoint.latitude == 15.33

    # Latitude > 90
    with pytest.raises(ValidationError) as exc_info:
        RouteEndpointSchema(
            id="acc_invalid_lat_high",
            name="Invalid Hotel",
            latitude=90.1,
            longitude=76.46,
        )
    assert "latitude" in str(exc_info.value)

    # Latitude < -90
    with pytest.raises(ValidationError) as exc_info:
        RouteEndpointSchema(
            id="acc_invalid_lat_low",
            name="Invalid Hotel",
            latitude=-90.1,
            longitude=76.46,
        )
    assert "latitude" in str(exc_info.value)

    # Longitude > 180
    with pytest.raises(ValidationError) as exc_info:
        RouteEndpointSchema(
            id="acc_invalid_lon_high",
            name="Invalid Hotel",
            latitude=15.33,
            longitude=180.1,
        )
    assert "longitude" in str(exc_info.value)

    # Longitude < -180
    with pytest.raises(ValidationError) as exc_info:
        RouteEndpointSchema(
            id="acc_invalid_lon_low",
            name="Invalid Hotel",
            latitude=15.33,
            longitude=-180.1,
        )
    assert "longitude" in str(exc_info.value)


def test_single_attraction_accommodation_round_trip():
    """
    TASK 2: Verify route with one attraction and an accommodation:
    - Exactly one attraction stop.
    - Departs from accommodation.
    - Returns to accommodation when return_to_accommodation=True.
    - Has expected origin and return legs.
    - No dummy TSP node appears as an attraction.
    """
    optimizer = IntraDayRouteOptimizer()
    attrs = create_sample_cluster_attractions()[:1]  # 1 attraction: Virupaksha Temple
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        attraction_count=1,
        centroid=ClusterCentroidSchema(latitude=attrs[0].latitude, longitude=attrs[0].longitude),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        is_low_utilization=True,
        attractions=attrs,
    )

    hotel = RouteEndpointSchema(
        id="acc_hampi_boulders",
        name="Hampi Boulders Resort",
        latitude=15.3600,
        longitude=76.4900,
        endpoint_type="accommodation",
    )

    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
        accommodation=hotel,
        return_to_accommodation=True,
    )

    schedule, deferred = optimizer.optimize_day_schedule(req)

    # 1. Exactly one attraction stop
    assert schedule.attraction_count == 1
    assert len(schedule.items) == 1
    assert len(schedule.ordered_attractions) == 1
    assert schedule.items[0].attraction.id == attrs[0].id

    # 2. Starts and ends at accommodation
    assert schedule.start_location_type == "accommodation"
    assert schedule.start_location_name == hotel.name
    assert schedule.end_location_type == "accommodation"
    assert schedule.end_location_name == hotel.name
    assert schedule.is_round_trip is True

    # 3. Has origin and return legs
    assert schedule.accommodation_origin_leg is not None
    assert schedule.accommodation_origin_leg.from_attraction_id == hotel.id
    assert schedule.accommodation_origin_leg.to_attraction_id == attrs[0].id
    assert schedule.accommodation_origin_leg.distance_km > 0.0

    assert schedule.accommodation_return_leg is not None
    assert schedule.accommodation_return_leg.from_attraction_id == attrs[0].id
    assert schedule.accommodation_return_leg.to_attraction_id == hotel.id
    assert schedule.accommodation_return_leg.distance_km > 0.0

    # 4. Total legs = 2 (hotel -> attraction, attraction -> hotel)
    assert len(schedule.legs) == 2

    # 5. No dummy TSP node in ordered attractions or items
    for item in schedule.items:
        assert item.attraction.id in [a.id for a in attrs]
    for attr in schedule.ordered_attractions:
        assert attr.id in [a.id for a in attrs]


def test_standalone_optimization_endpoint_rejects_mismatched_accommodation(client, db_session):
    """
    TASK 3: Verify the standalone optimization endpoint rejects an accommodation
    whose database destination does not match the requested destination.
    """
    seed_database(db_session)

    attrs = create_sample_cluster_attractions()[:2]
    clusters = [
        {
            "cluster_id": 0,
            "day_number": 1,
            "attraction_count": len(attrs),
            "attractions": [a.model_dump() for a in attrs],
            "centroid": {"latitude": 15.33, "longitude": 76.46},
            "avg_distance_to_centroid_km": 1.0,
            "max_distance_to_centroid_km": 2.0,
            "dispersion_km": 2.0,
            "is_low_utilization": False,
        }
    ]

    # Destination is 'hampi', but accommodation ID is from 'coorg' (seeded in database)
    payload = {
        "destination_id": "hampi",
        "clusters": clusters,
        "preferred_transport": "auto",
        "pace": "Moderate",
        "day_start_time": "09:00",
        "accommodation": {
            "id": "coorg-heritage-resort",  # Belongs to destination 'coorg' in database
            "name": "Heritage Resort Madikeri",
            "latitude": 12.4590,
            "longitude": 75.7025,
            "endpoint_type": "accommodation",
        },
        "return_to_accommodation": True,
    }

    res = client.post("/api/v1/optimization/route", json=payload)
    # Must fail with 422 Unprocessable Entity due to OptimizationConstraintException
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = res.json()
    assert "does not match the requested destination" in str(data["detail"])


def test_group_admission_fee_multiplied_by_party_size():
    """Verify that route optimizer multiplies admission fee by party size for group totals."""
    optimizer = IntraDayRouteOptimizer()
    attr = Attraction(
        id="paid_monument",
        destination_id="hampi",
        category="heritage",
        name="Paid Monument",
        description="Ticketed Monument",
        latitude=15.335,
        longitude=76.460,
        average_visit_duration=1.5,
        entry_fee=50.0,
        popularity_score=0.8,
        rating=4.5,
        opening_time="08:00:00",
        closing_time="18:00:00",
        duration_estimation_method="curated_empirical_average",
    )
    cluster = ClusterDaySchema(
        cluster_id=0,
        day_number=1,
        centroid=ClusterCentroidSchema(latitude=15.335, longitude=76.460),
        avg_distance_to_centroid_km=0.0,
        max_distance_to_centroid_km=0.0,
        dispersion_km=0.0,
        attraction_count=1,
        attractions=[AttractionResponse.model_validate(attr)],
    )

    # Party size of 4
    req = DayOptimizationRequest(
        destination_id="hampi",
        day_number=1,
        cluster=cluster,
        preferred_transport="auto",
        pace="Moderate",
        party_size=4,
    )
    schedule, deferred = optimizer.optimize_day_schedule(req)
    assert len(schedule.items) == 1
    item = schedule.items[0]
    # Per-person fee is 50.0
    assert item.item_admission_fee == 50.0
    # Group fee for party of 4 is 200.0
    assert item.item_group_admission_fee == 200.0
    assert item.admission_fee_status == "paid"
    # Day total admission cost is 200.0
    assert schedule.day_estimated_admission_cost == 200.0
    assert schedule.day_total_estimated_cost >= 200.0
