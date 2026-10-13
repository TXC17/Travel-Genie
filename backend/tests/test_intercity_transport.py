"""
Unit and Integration Tests for Intelligent Intercity Transportation Recommendations.
Covers deterministic pricing, duration, group scalability, budget compatibility,
fallback Haversine estimation, mode availability constraints, and API contract validation.
"""

import pytest
from fastapi import status
from app.services.intercity_transport_service import IntercityTransportService
from app.schemas.transport import (
    TransportModeEnum,
    VerificationStatusEnum,
    BudgetCompatibilityEnum,
    IntercityRecommendationRequest,
)


@pytest.fixture
def transport_service():
    return IntercityTransportService()


# 1. Valid origin and destination inputs
def test_valid_origin_and_destination(transport_service):
    req = IntercityRecommendationRequest(
        origin="Bengaluru",
        destination="Hampi",
        party_size=2,
        budget=10000.0,
    )
    res = transport_service.get_recommendations(req)

    assert res.origin == "Bengaluru"
    assert res.destination_id == "hampi"
    assert res.party_size == 2
    assert len(res.options) == 6
    assert res.available_count > 0

    modes = [o.transport_mode for o in res.options]
    assert TransportModeEnum.CAR in modes
    assert TransportModeEnum.BUS in modes
    assert TransportModeEnum.TRAIN in modes


# 2. Invalid or missing inputs (unsupported destination, empty origin)
def test_unsupported_destination(transport_service):
    req = IntercityRecommendationRequest(
        origin="Bengaluru",
        destination="Paris",
        party_size=2,
    )
    with pytest.raises(Exception) as exc_info:
        transport_service.get_recommendations(req)
    assert "Unsupported destination" in str(exc_info.value)


# 3. Different group sizes & vehicle scaling
def test_group_size_vehicle_scaling(transport_service):
    # Solo traveler
    res_solo = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Coorg", party_size=1)
    )
    car_solo = next(o for o in res_solo.options if o.transport_mode == TransportModeEnum.CAR)

    # 6 travelers (requires 2 standard cars)
    res_group = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Coorg", party_size=6)
    )
    car_group = next(o for o in res_group.options if o.transport_mode == TransportModeEnum.CAR)

    assert car_group.estimated_total_cost > car_solo.estimated_total_cost
    assert car_group.group_suitability_label in ["Good", "Moderate"]
    assert "2 standard vehicles" in car_group.group_suitability_notes


# 4. Budget-aware ranking
def test_budget_aware_ranking(transport_service):
    # Tight budget: ₹1,500 for 2 people to Hampi
    res_tight = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Hampi", party_size=2, budget=1500.0)
    )
    # Generous budget: ₹50,000 for 2 people to Hampi
    res_generous = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Hampi", party_size=2, budget=50000.0)
    )

    car_tight = next(o for o in res_tight.options if o.transport_mode == TransportModeEnum.CAR)
    assert car_tight.budget_compatibility == BudgetCompatibilityEnum.OVER_BUDGET
    assert "exceeds" in car_tight.recommendation_reason.lower()

    # In generous budget, train or bus or car is within budget
    train_gen = next(o for o in res_generous.options if o.transport_mode == TransportModeEnum.TRAIN)
    assert train_gen.budget_compatibility == BudgetCompatibilityEnum.WITHIN_BUDGET


# 5. Cost calculations and group breakdown
def test_cost_calculations_consistency(transport_service):
    res = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Hampi", party_size=4)
    )
    bus = next(o for o in res.options if o.transport_mode == TransportModeEnum.BUS)

    assert bus.estimated_total_cost is not None
    assert bus.estimated_cost_per_person is not None
    assert round(bus.estimated_cost_per_person * 4, 2) == bus.estimated_total_cost
    assert bus.cost_per_km is not None and bus.cost_per_km > 0.0


# 6. Fallback estimation for arbitrary origin
def test_fallback_estimation_for_unknown_origin(transport_service):
    res = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Solapur", destination="Hampi", party_size=2)
    )
    assert res.destination_id == "hampi"
    car = next(o for o in res.options if o.transport_mode == TransportModeEnum.CAR)
    assert car.verification_status == VerificationStatusEnum.ESTIMATED
    assert car.distance_type == "estimated_road_winding"
    assert "detour" in car.data_provenance.get("source", "").lower() or "winding" in car.data_provenance.get("source", "").lower()


# 7. Unsupported transportation modes (Boat to inland destinations)
def test_boat_unavailability_for_inland_destinations(transport_service):
    # Hampi is inland
    res_hampi = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Hampi", party_size=2)
    )
    boat_hampi = next(o for o in res_hampi.options if o.transport_mode == TransportModeEnum.BOAT)
    assert not boat_hampi.is_available
    assert boat_hampi.verification_status == VerificationStatusEnum.UNAVAILABLE
    assert "inland" in boat_hampi.unavailability_reason.lower() or "waterway" in boat_hampi.unavailability_reason.lower()

    # Coorg is inland
    res_coorg = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Coorg", party_size=2)
    )
    boat_coorg = next(o for o in res_coorg.options if o.transport_mode == TransportModeEnum.BOAT)
    assert not boat_coorg.is_available

    # Dandeli is inland
    res_dandeli = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Dandeli", party_size=2)
    )
    boat_dandeli = next(o for o in res_dandeli.options if o.transport_mode == TransportModeEnum.BOAT)
    assert not boat_dandeli.is_available


# 8. Verified status for curated routes
def test_verified_status_for_curated_routes(transport_service):
    res = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Bengaluru", destination="Hampi", party_size=2)
    )
    car = next(o for o in res.options if o.transport_mode == TransportModeEnum.CAR)
    assert car.verification_status == VerificationStatusEnum.VERIFIED
    assert car.distance_type == "verified_road"
    assert car.distance_km == 342.0


# 9. Flight viability threshold for short routes
def test_flight_unavailability_for_short_distances(transport_service):
    # Mysuru to Coorg is ~118 km (short distance)
    res = transport_service.get_recommendations(
        IntercityRecommendationRequest(origin="Mysuru", destination="Coorg", party_size=2)
    )
    flight = next(o for o in res.options if o.transport_mode == TransportModeEnum.FLIGHT)
    assert not flight.is_available
    assert "short" in flight.unavailability_reason.lower() or "threshold" in flight.unavailability_reason.lower()


# 10. Deterministic reproducibility
def test_deterministic_reproducibility(transport_service):
    req = IntercityRecommendationRequest(origin="Pune", destination="Goa", party_size=3, budget=12000.0)
    res1 = transport_service.get_recommendations(req)
    res2 = transport_service.get_recommendations(req)

    assert [o.transport_mode for o in res1.options] == [o.transport_mode for o in res2.options]
    assert [o.score for o in res1.options] == [o.score for o in res2.options]
    assert [o.estimated_total_cost for o in res1.options] == [o.estimated_total_cost for o in res2.options]


# 11. Edge cases: identical origin and destination
def test_identical_origin_and_destination_error(transport_service):
    req = IntercityRecommendationRequest(origin="Hampi", destination="Hampi", party_size=2)
    with pytest.raises(Exception) as exc_info:
        transport_service.get_recommendations(req)
    assert "identical" in str(exc_info.value).lower() or "local" in str(exc_info.value).lower()


# 12. API Endpoint Integration Test via TestClient
def test_intercity_api_endpoints(client):
    # Test GET endpoint with query parameters
    get_res = client.get("/api/v1/transport/intercity-recommendations?origin=Bengaluru&destination=coorg&party_size=2&budget=12000")
    assert get_res.status_code == status.HTTP_200_OK
    data = get_res.json()
    assert data["origin"] == "Bengaluru"
    assert data["destination_id"] == "coorg"
    assert len(data["options"]) == 6
    assert data["fastest_mode"] is not None
    assert data["cheapest_mode"] is not None

    # Test POST endpoint with JSON body
    post_payload = {
        "origin": "Mumbai",
        "destination": "Goa",
        "party_size": 4,
        "budget": 20000.0,
    }
    post_res = client.post("/api/v1/transport/intercity-recommendations", json=post_payload)
    assert post_res.status_code == status.HTTP_200_OK
    post_data = post_res.json()
    assert post_data["origin"] == "Mumbai"
    assert post_data["destination_id"] == "goa"
    assert post_data["party_size"] == 4

    # Test validation error on party size <= 0
    inv_res = client.get("/api/v1/transport/intercity-recommendations?origin=Bengaluru&destination=coorg&party_size=0")
    assert inv_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test validation error on party size > 50
    inv_res2 = client.get("/api/v1/transport/intercity-recommendations?origin=Bengaluru&destination=coorg&party_size=55")
    assert inv_res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test validation error on empty origin
    inv_res3 = client.get("/api/v1/transport/intercity-recommendations?origin=%20&destination=coorg")
    assert inv_res3.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
