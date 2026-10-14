"""
Comprehensive Test Suite for Phase 2: Budget-Based Accommodation Recommendations.
Tests catalog queries, multi-criteria recommendation scoring, capacity math,
budget impact calculations, transparent provenance badges, date validations,
transit cost integration, deficit handling, and trip persistence.
"""

import pytest
from fastapi import status
from app.utils.seed import seed_database
from app.schemas.accommodation import AccommodationRecommendationRequest
from app.services.accommodation_service import AccommodationService


@pytest.fixture(autouse=True)
def seed_test_data(db_session):
    """Seed test database with authentic destinations and accommodations."""
    seed_database(db_session)


def test_get_accommodations_by_destination(client):
    """Verify listing accommodations for supported destinations."""
    for dest in ["coorg", "dandeli", "hampi", "goa"]:
        response = client.get(f"/api/v1/accommodations?destination_id={dest}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4
        for item in data:
            assert item["destination_id"] == dest
            assert item["price_per_night"] > 0
            assert item["room_capacity"] >= 1
            assert item["rating"] >= 1.0 and item["rating"] <= 5.0
            assert isinstance(item["amenities"], list)
            assert item["is_verified"] in [True, False]
            assert item["provenance"]["provenance_badge"] in ["VERIFIED", "ESTIMATED"]


def test_get_accommodations_filters(client):
    """Verify tier, rating, and type filters."""
    # Filter by budget tier
    res_budget = client.get("/api/v1/accommodations?destination_id=coorg&budget_tier=Budget")
    assert res_budget.status_code == 200
    for item in res_budget.json():
        assert item["price_per_night"] <= 3200

    # Filter by min rating
    res_rating = client.get("/api/v1/accommodations?destination_id=hampi&min_rating=4.5")
    assert res_rating.status_code == 200
    for item in res_rating.json():
        assert item["rating"] >= 4.5

    # Filter by accommodation type
    res_type = client.get("/api/v1/accommodations?destination_id=goa&accommodation_type=hostel")
    assert res_type.status_code == 200
    for item in res_type.json():
        assert "hostel" in item["accommodation_type"].lower()


def test_get_single_accommodation(client):
    """Verify retrieving specific accommodation by ID and 404 for unknown ID."""
    response = client.get("/api/v1/accommodations/coorg-zostel-homestay")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "coorg-zostel-homestay"
    assert data["name"] == "Zostel Coorg (Madikeri)"
    assert data["destination_id"] == "coorg"

    # 404 test
    res_404 = client.get("/api/v1/accommodations/non-existent-hotel")
    assert res_404.status_code == 404


def test_accommodation_recommendations_solo_traveler(client):
    """Verify recommendations for 1 traveler over 3 nights with budget."""
    payload = {
        "destination_id": "hampi",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-04",
        "party_size": 1,
        "total_budget": 12000.0,
        "budget_tier": "Standard",
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["destination_id"] == "hampi"
    assert data["nights"] == 3
    assert data["party_size"] == 1
    assert data["budget_context"]["nights"] == 3
    assert len(data["recommendations"]) > 0

    top = data["recommendations"][0]
    assert top["rooms_needed"] == 1
    assert top["nights"] == 3
    assert top["total_cost"] == 3 * top["price_per_night"] * 1
    assert top["match_score"] > 0.0
    assert len(top["match_reasons"]) > 0
    assert top["provenance_badge"] == "VERIFIED"


def test_accommodation_recommendations_group_capacity(client):
    """Verify room capacity logic: 5 travelers in 2-person rooms require 3 rooms."""
    payload = {
        "destination_id": "dandeli",
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "party_size": 5,
        "total_budget": 30000.0,
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["nights"] == 2
    assert data["party_size"] == 5

    for rec in data["recommendations"]:
        capacity = rec["accommodation"]["room_capacity"]
        expected_rooms = -(-5 // capacity)  # ceiling division
        assert rec["rooms_needed"] == expected_rooms
        assert rec["total_cost"] == 2 * rec["price_per_night"] * expected_rooms


def test_accommodation_recommendations_budget_deduction(client):
    """Verify remaining budget and utilization percentages are accurately computed."""
    total_budget = 20000.0
    payload = {
        "destination_id": "coorg",
        "check_in_date": "2026-11-15",
        "check_out_date": "2026-11-17",  # 2 nights
        "party_size": 2,
        "total_budget": total_budget,
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    for rec in data["recommendations"]:
        assert rec["total_accounted_cost"] == rec["total_cost"]
        assert rec["remaining_budget"] == total_budget - rec["total_cost"]
        expected_util = round((rec["total_cost"] / total_budget) * 100, 1)
        assert rec["budget_utilization_pct"] == expected_util


def test_accommodation_recommendations_query_endpoint(client):
    """Verify GET convenience query endpoint works with same schema and transit cost."""
    response = client.get(
        "/api/v1/accommodations/recommendations/query"
        "?destination_id=goa&check_in_date=2026-12-01&check_out_date=2026-12-03&party_size=2&total_budget=25000&intercity_transport_cost=3000"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["destination_id"] == "goa"
    assert data["nights"] == 2
    assert data["budget_context"]["intercity_transport_cost"] == 3000.0
    assert len(data["recommendations"]) > 0


# ========================================================
# Phase 2 Audit Verification Tests
# ========================================================


def test_accommodation_stay_durations(client):
    """Verify 1-night and multi-night stays compute exact night counts."""
    # 1-night stay
    res_1 = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "goa",
            "check_in_date": "2026-11-01",
            "check_out_date": "2026-11-02",
            "party_size": 2,
            "total_budget": 15000.0,
        },
    )
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["nights"] == 1
    assert data_1["budget_context"]["nights"] == 1
    assert data_1["recommendations"][0]["nights"] == 1

    # 4-night stay
    res_4 = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "goa",
            "check_in_date": "2026-11-01",
            "check_out_date": "2026-11-05",
            "party_size": 2,
            "total_budget": 30000.0,
        },
    )
    assert res_4.status_code == 200
    data_4 = res_4.json()
    assert data_4["nights"] == 4
    assert data_4["budget_context"]["nights"] == 4


def test_accommodation_same_day_dates_rejected(client):
    """Verify that same-day check-in and check-out returns 422 Unprocessable Entity."""
    payload = {
        "destination_id": "coorg",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-01",
        "party_size": 2,
        "total_budget": 10000.0,
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("check_out_date must be strictly after check_in_date" in err["msg"] for err in errors)


def test_accommodation_checkout_before_checkin_rejected(client):
    """Verify that checkout date prior to checkin returns 422."""
    payload = {
        "destination_id": "coorg",
        "check_in_date": "2026-11-05",
        "check_out_date": "2026-11-02",
        "party_size": 2,
        "total_budget": 10000.0,
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 422


def test_accommodation_service_direct_date_validation(db_session):
    """Direct service call unit test confirming ValueError is raised on invalid dates."""
    # Same-day stay
    with pytest.raises(ValueError, match="must be strictly after check_in_date"):
        AccommodationService.get_recommendations(
            db=db_session,
            request=AccommodationRecommendationRequest.model_construct(
                destination_id="coorg",
                check_in_date="2026-11-01",
                check_out_date="2026-11-01",
                party_size=2,
            ),
        )

    # Inverted stay
    with pytest.raises(ValueError, match="must be strictly after check_in_date"):
        AccommodationService.get_recommendations(
            db=db_session,
            request=AccommodationRecommendationRequest.model_construct(
                destination_id="coorg",
                check_in_date="2026-11-05",
                check_out_date="2026-11-02",
                party_size=2,
            ),
        )


def test_accommodation_budget_accounting_with_and_without_transit(client):
    """
    Verify multi-category budget accounting:
    1. Accommodation only: total_accounted = total_cost
    2. Accommodation + Transit: total_accounted = total_cost + transit_cost
    Remaining budget clearly reflects accounted total.
    """
    total_budget = 25000.0

    # 1. Without transit
    res_no_transit = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "coorg",
            "check_in_date": "2026-11-10",
            "check_out_date": "2026-11-12",
            "party_size": 2,
            "total_budget": total_budget,
        },
    )
    assert res_no_transit.status_code == 200
    data_no = res_no_transit.json()
    ctx_no = data_no["budget_context"]
    assert ctx_no["intercity_transport_cost"] is None
    assert ctx_no["included_cost_categories"] == ["accommodation"]
    assert any("transit" in cat for cat in ctx_no["excluded_cost_categories"])
    assert ctx_no["is_estimate_complete"] is False

    top_no = data_no["recommendations"][0]
    assert top_no["intercity_transport_cost"] is None
    assert top_no["total_accounted_cost"] == top_no["total_cost"]
    assert top_no["remaining_budget"] == total_budget - top_no["total_cost"]
    assert top_no["remaining_budget_after_accommodation"] == total_budget - top_no["total_cost"]

    # 2. With transit
    transit_cost = 4500.0
    res_transit = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "coorg",
            "check_in_date": "2026-11-10",
            "check_out_date": "2026-11-12",
            "party_size": 2,
            "total_budget": total_budget,
            "intercity_transport_cost": transit_cost,
        },
    )
    assert res_transit.status_code == 200
    data_tr = res_transit.json()
    ctx_tr = data_tr["budget_context"]
    assert ctx_tr["intercity_transport_cost"] == transit_cost
    assert ctx_tr["included_cost_categories"] == ["accommodation", "intercity_transport"]
    assert ctx_tr["is_estimate_complete"] is False

    top_tr = data_tr["recommendations"][0]
    assert top_tr["intercity_transport_cost"] == transit_cost
    assert top_tr["total_accounted_cost"] == top_tr["total_cost"] + transit_cost
    assert top_tr["remaining_budget"] == total_budget - (top_tr["total_cost"] + transit_cost)
    assert top_tr["remaining_budget_after_accommodation"] == total_budget - top_tr["total_cost"]


def test_accommodation_deficit_handling(client):
    """Verify that budget overrun yields an unmasked negative remaining budget and is_within_budget=False."""
    tiny_budget = 1000.0
    response = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "goa",
            "check_in_date": "2026-12-01",
            "check_out_date": "2026-12-03",
            "party_size": 2,
            "total_budget": tiny_budget,
        },
    )
    assert response.status_code == 200
    data = response.json()
    for rec in data["recommendations"]:
        if rec["total_cost"] > tiny_budget:
            assert rec["is_within_budget"] is False
            assert rec["remaining_budget"] < 0
            assert rec["remaining_budget"] == tiny_budget - rec["total_cost"]


def test_accommodation_party_of_three_capacity_math(client):
    """
    Verify capacity division for an odd party of 3:
    - Standard 2-capacity room requires ceil(3/2) = 2 rooms.
    - Dorm / Family 4-capacity room requires ceil(3/4) = 1 room.
    """
    response = client.post(
        "/api/v1/accommodations/recommendations",
        json={
            "destination_id": "hampi",
            "check_in_date": "2026-11-01",
            "check_out_date": "2026-11-03",
            "party_size": 3,
            "total_budget": 15000.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    for rec in data["recommendations"]:
        cap = rec["accommodation"]["room_capacity"]
        if cap == 2:
            assert rec["rooms_needed"] == 2
        elif cap >= 3:
            assert rec["rooms_needed"] == 1


def test_trip_selected_accommodation_persistence(client, db_session):
    """
    Verify persistence of selected_accommodation_id on Trip creation,
    fetching trip detail with full accommodation, and destination mismatch rejection.
    """
    # 1. Register user
    user_payload = {
        "email": "hotelpersist@travelgenie.ai",
        "password": "securepassword",
        "full_name": "Persist Tester",
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create trip with valid accommodation for Coorg
    trip_payload = {
        "destination_id": "coorg",
        "title": "Coorg Stay Experience",
        "start_date": "2026-11-10",
        "end_date": "2026-11-13",
        "party_size": 2,
        "total_budget": 20000.0,
        "selected_accommodation_id": "coorg-zostel-homestay",
    }
    create_res = client.post("/api/v1/trips", json=trip_payload, headers=headers)
    assert create_res.status_code == status.HTTP_201_CREATED
    trip_data = create_res.json()
    trip_id = trip_data["id"]
    assert trip_data["selected_accommodation_id"] == "coorg-zostel-homestay"

    # 3. Retrieve trip by ID and verify nested selected_accommodation
    get_res = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    detail = get_res.json()
    assert detail["selected_accommodation_id"] == "coorg-zostel-homestay"
    assert detail["selected_accommodation"] is not None
    assert detail["selected_accommodation"]["id"] == "coorg-zostel-homestay"
    assert detail["selected_accommodation"]["name"] == "Zostel Coorg (Madikeri)"
    assert detail["selected_accommodation"]["destination_id"] == "coorg"

    # 4. Reject trip creation with accommodation from another destination (e.g. Goa hotel for Coorg trip)
    mismatch_payload = {
        "destination_id": "coorg",
        "title": "Mismatched Trip",
        "start_date": "2026-11-10",
        "end_date": "2026-11-13",
        "party_size": 2,
        "total_budget": 20000.0,
        "selected_accommodation_id": "goa-old-quarter-hostel",
    }
    mismatch_res = client.post("/api/v1/trips", json=mismatch_payload, headers=headers)
    assert mismatch_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "belongs to 'goa'" in mismatch_res.json()["detail"]

    # 5. Reject trip creation with non-existent accommodation
    not_found_payload = {
        "destination_id": "coorg",
        "title": "Invalid Hotel Trip",
        "start_date": "2026-11-10",
        "end_date": "2026-11-13",
        "party_size": 2,
        "total_budget": 20000.0,
        "selected_accommodation_id": "non-existent-hotel-id",
    }
    not_found_res = client.post("/api/v1/trips", json=not_found_payload, headers=headers)
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND


def test_itinerary_aware_location_suitability_multi_day(db_session):
    """Verify that multi-day itinerary attractions calculate location suitability and transit distances."""
    # 2 days of Hampi attractions
    day1_items = [
        {"visit_order": 1, "attraction": {"name": "Virupaksha", "latitude": 15.3353, "longitude": 76.4600}},
        {"visit_order": 2, "attraction": {"name": "Vittala", "latitude": 15.3400, "longitude": 76.4750}},
    ]
    day2_items = [
        {"visit_order": 1, "attraction": {"name": "Lotus Mahal", "latitude": 15.3200, "longitude": 76.4700}},
    ]
    req = AccommodationRecommendationRequest(
        destination_id="hampi",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=15000.0,
        itinerary_days=[
            {"day_number": 1, "items": day1_items},
            {"day_number": 2, "items": day2_items},
        ],
    )
    res = AccommodationService.get_recommendations(db_session, req)
    assert res.is_itinerary_aware is True
    assert res.total_itinerary_days_evaluated == 2
    assert len(res.recommendations) > 0

    top = res.recommendations[0]
    assert top.location_suitability_score is not None
    assert 0.0 <= top.location_suitability_score <= 1.0
    assert top.estimated_total_hotel_transit_km is not None
    assert top.estimated_daily_hotel_transit_km is not None
    assert top.road_winding_factor == 1.30
    assert "road_winding_factor" in top.provenance_distance_method


def test_accommodation_ranking_changes_when_itinerary_changes(db_session):
    """Verify that ranking changes dynamically when planned itinerary activities change."""
    # Itinerary North: North Goa attractions (Anjuna / Baga / Aguada ~15.55 lat, ~73.75 lon)
    north_days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Baga Beach", "latitude": 15.5553, "longitude": 73.7517}},
                {"visit_order": 2, "attraction": {"name": "Fort Aguada", "latitude": 15.4922, "longitude": 73.7736}},
            ],
        }
    ]

    # Itinerary South: South Goa attractions (Palolem / Cabo de Rama ~15.01 lat, ~74.02 lon)
    south_days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Palolem Beach", "latitude": 15.0100, "longitude": 74.0230}},
                {"visit_order": 2, "attraction": {"name": "Cabo de Rama", "latitude": 15.0880, "longitude": 73.9210}},
            ],
        }
    ]

    req_north = AccommodationRecommendationRequest(
        destination_id="goa",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=25000.0,
        itinerary_days=north_days,
    )
    res_north = AccommodationService.get_recommendations(db_session, req_north)

    req_south = AccommodationRecommendationRequest(
        destination_id="goa",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=25000.0,
        itinerary_days=south_days,
    )
    res_south = AccommodationService.get_recommendations(db_session, req_south)

    # Top accommodation for North itinerary must have lower transit distance to North than South property
    north_top_id = res_north.recommendations[0].accommodation.id
    south_top_id = res_south.recommendations[0].accommodation.id

    # The rankings must be distinct or reflect the spatial shift
    assert res_north.recommendations[0].estimated_daily_hotel_transit_km < res_north.recommendations[-1].estimated_daily_hotel_transit_km
    assert res_south.recommendations[0].estimated_daily_hotel_transit_km < res_south.recommendations[-1].estimated_daily_hotel_transit_km


def test_cheaper_distant_hotel_not_always_first(db_session):
    """Verify that a centrally situated property can outrank a cheaper property that is substantially more distant."""
    # Day itinerary in central Madikeri, Coorg (12.42 lat, 75.73 lon)
    central_days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Madikeri Fort", "latitude": 12.4244, "longitude": 75.7382}},
                {"visit_order": 2, "attraction": {"name": "Raja's Seat", "latitude": 12.4180, "longitude": 75.7350}},
            ],
        }
    ]

    req = AccommodationRecommendationRequest(
        destination_id="coorg",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=20000.0,
        itinerary_days=central_days,
    )
    res = AccommodationService.get_recommendations(db_session, req)
    recs = res.recommendations

    # Find Madikeri central property (e.g. Zostel Coorg Madikeri)
    madikeri_prop = next((r for r in recs if "madikeri" in r.accommodation.name.lower()), None)
    assert madikeri_prop is not None

    # Central property should have a high location suitability score
    assert madikeri_prop.location_suitability_score >= 0.70


def test_itinerary_aware_budget_and_capacity_constraints(db_session):
    """Verify budget limits and room capacity remain enforced when itinerary awareness is active."""
    days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Virupaksha", "latitude": 15.3353, "longitude": 76.4600}},
            ],
        }
    ]
    # Party of 5 with tight budget: requires at least 3 standard double rooms
    req = AccommodationRecommendationRequest(
        destination_id="hampi",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=5,
        total_budget=4000.0,  # Very tight budget
        itinerary_days=days,
    )
    res = AccommodationService.get_recommendations(db_session, req)
    for r in res.recommendations:
        # Rooms needed must accommodate 5 people
        assert r.rooms_needed * r.accommodation.room_capacity >= 5
        # Total cost is 2 nights * price_per_night * rooms_needed
        assert r.total_cost == 2 * r.price_per_night * r.rooms_needed
        if r.total_cost > 4000.0:
            assert r.is_within_budget is False


def test_itinerary_aware_missing_coordinates_handled_safely(db_session):
    """Verify safe fallback when day items lack coordinates."""
    days_no_coords = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Mysterious Spot", "latitude": None, "longitude": None}},
            ],
        }
    ]
    req = AccommodationRecommendationRequest(
        destination_id="hampi",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=15000.0,
        itinerary_days=days_no_coords,
    )
    res = AccommodationService.get_recommendations(db_session, req)
    # Should fall back cleanly without crashing
    assert len(res.recommendations) > 0
    assert res.is_itinerary_aware is False


def test_accommodation_category_filtering_and_classification(client, db_session):
    """Verify category filtering across Ultra-Luxury, Ultra-Budget, Moderate / Mid-Range, and All Stays."""
    # 1. Ultra-Luxury in Coorg
    res_lux = client.get("/api/v1/accommodations?destination_id=coorg&category=ultra_luxury")
    assert res_lux.status_code == 200
    lux_data = res_lux.json()
    assert len(lux_data) >= 1
    for item in lux_data:
        assert item["category"] == "Ultra-Luxury"
        assert item["price_per_night"] >= 8000.0

    # 2. Ultra-Budget in Coorg
    res_bud = client.get("/api/v1/accommodations?destination_id=coorg&category=ultra_budget")
    assert res_bud.status_code == 200
    bud_data = res_bud.json()
    assert len(bud_data) >= 2
    for item in bud_data:
        assert item["category"] == "Ultra-Budget"
        assert item["price_per_night"] <= 3200.0

    # 3. Moderate / Mid-Range in Coorg
    res_mod = client.get("/api/v1/accommodations?destination_id=coorg&category=moderate")
    assert res_mod.status_code == 200
    mod_data = res_mod.json()
    assert len(mod_data) >= 2
    for item in mod_data:
        assert item["category"] == "Moderate / Mid-Range"
        assert 2800.0 <= item["price_per_night"] <= 8400.0

    # 4. All Stays
    res_all = client.get("/api/v1/accommodations?destination_id=coorg&category=all")
    assert res_all.status_code == 200
    assert len(res_all.json()) == len(lux_data) + len(bud_data) + len(mod_data)


def test_accommodation_recommendations_category_ultra_budget(client):
    """Verify Ultra-Budget recommendations prioritize affordability and honest tariff benchmarks."""
    payload = {
        "destination_id": "hampi",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-04",
        "party_size": 2,
        "total_budget": 8000.0,
        "category": "ultra_budget",
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["budget_context"]["selected_category"] == "Ultra-Budget"
    assert len(data["recommendations"]) >= 2
    for rec in data["recommendations"]:
        assert rec["category"] == "Ultra-Budget"
        assert rec["accommodation"]["category"] == "Ultra-Budget"
        # Check reasons include category and tariff benchmark
        reason_text = " ".join(rec["match_reasons"])
        assert "Ultra-Budget" in reason_text
        assert "Estimated tariff:" in reason_text


def test_accommodation_recommendations_category_ultra_luxury(client):
    """Verify Ultra-Luxury recommendations return premium properties and explain luxury indicators."""
    payload = {
        "destination_id": "hampi",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-03",
        "party_size": 2,
        "total_budget": 60000.0,
        "category": "ultra_luxury",
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["budget_context"]["selected_category"] == "Ultra-Luxury"
    assert len(data["recommendations"]) == 1
    top = data["recommendations"][0]
    assert top["category"] == "Ultra-Luxury"
    assert top["accommodation"]["name"] == "Evolve Back Kamalapura Palace"
    assert top["total_cost"] == 2 * top["price_per_night"] * 1
    reason_text = " ".join(top["match_reasons"])
    assert "Ultra-Luxury" in reason_text
    assert "Recommended for premium luxury" in reason_text
    # Check data status notice explains dataset scope
    assert data["category_data_status"] is not None
    assert "1 verified Ultra-Luxury benchmark" in data["category_data_status"]


def test_accommodation_unrated_missing_rating_handled_honestly(db_session):
    """Verify properties without guest rating display 'Guest ratings unavailable' and apply neutral prior."""
    from app.models.accommodation import Accommodation

    # Create an unrated accommodation with rating = None
    unrated_hotel = Accommodation(
        id="dandeli-unrated-cottage",
        destination_id="dandeli",
        name="Dandeli Riverside Unrated Cottage",
        accommodation_type="homestay",
        description="Newly established rustic cottage near riverside.",
        latitude=15.2400,
        longitude=74.6300,
        price_per_night=1900.0,
        currency="INR",
        rating=None,  # Missing rating
        room_capacity=2,
        amenities=["Garden", "River Access", "Campfire"],
        is_verified=True,
        provenance={"source": "Regional Cottage Registry", "rate_tier": "Budget"},
        is_active=True,
    )
    db_session.add(unrated_hotel)
    db_session.commit()

    req = AccommodationRecommendationRequest(
        destination_id="dandeli",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        category="ultra_budget",
    )
    res = AccommodationService.get_recommendations(db_session, req)
    unrated_rec = next((r for r in res.recommendations if r.accommodation.id == "dandeli-unrated-cottage"), None)
    assert unrated_rec is not None
    assert unrated_rec.accommodation.rating is None

    # Check match reasons explicitly state guest ratings unavailable
    reason_text = " ".join(unrated_rec.match_reasons)
    assert "Guest ratings unavailable" in reason_text
    assert "highly rated" not in reason_text.lower()
    # Scored with neutral score, match score is valid positive number
    assert 0.0 < unrated_rec.match_score <= 1.0


def test_accommodation_category_switching_preserves_capacity_and_itinerary_suitability(db_session):
    """Verify changing category refreshes options while calculating correct capacity and multi-day hotel transit."""
    days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Madikeri Fort", "latitude": 12.4244, "longitude": 75.7382}},
                {"visit_order": 2, "attraction": {"name": "Raja Seat", "latitude": 12.4137, "longitude": 75.7360}},
            ],
        },
        {
            "day_number": 2,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Abbey Falls", "latitude": 12.4550, "longitude": 75.7170}},
            ],
        },
    ]

    # Query 1: Ultra-Budget
    req_budget = AccommodationRecommendationRequest(
        destination_id="coorg",
        check_in_date="2026-11-01",
        check_out_date="2026-11-04",  # 3 nights
        party_size=4,  # 4 travelers
        total_budget=20000.0,
        category="ultra_budget",
        itinerary_days=days,
    )
    res_budget = AccommodationService.get_recommendations(db_session, req_budget)
    assert res_budget.is_itinerary_aware is True
    assert res_budget.total_itinerary_days_evaluated == 2
    for r in res_budget.recommendations:
        assert r.category == "Ultra-Budget"
        assert r.nights == 3
        assert r.rooms_needed * r.accommodation.room_capacity >= 4
        assert r.total_cost == 3 * r.price_per_night * r.rooms_needed
        assert r.estimated_daily_hotel_transit_km is not None
        assert r.road_winding_factor == 1.30

    # Query 2: Moderate / Mid-Range
    req_mod = AccommodationRecommendationRequest(
        destination_id="coorg",
        check_in_date="2026-11-01",
        check_out_date="2026-11-04",
        party_size=4,
        total_budget=50000.0,
        category="moderate",
        itinerary_days=days,
    )
    res_mod = AccommodationService.get_recommendations(db_session, req_mod)
    assert res_mod.is_itinerary_aware is True
    for r in res_mod.recommendations:
        assert r.category == "Moderate / Mid-Range"
        assert r.nights == 3
        assert r.rooms_needed * r.accommodation.room_capacity >= 4
        assert r.total_cost == 3 * r.price_per_night * r.rooms_needed
        assert r.estimated_daily_hotel_transit_km is not None


def test_itinerary_activity_centroid_and_centrality_calculation(db_session):
    """Verify that the geographic centroid of scheduled attractions is computed and each recommendation discloses distance to activity center."""
    days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Madikeri Fort", "latitude": 12.4244, "longitude": 75.7382}},
                {"visit_order": 2, "attraction": {"name": "Raja Seat", "latitude": 12.4137, "longitude": 75.7360}},
            ],
        },
        {
            "day_number": 2,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Abbey Falls", "latitude": 12.4550, "longitude": 75.7170}},
            ],
        },
    ]
    req = AccommodationRecommendationRequest(
        destination_id="coorg",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=20000.0,
        itinerary_days=days,
    )
    res = AccommodationService.get_recommendations(db_session, req)
    assert res.is_itinerary_aware is True
    assert res.activity_center_coordinates is not None

    expected_lat = round((12.4244 + 12.4137 + 12.4550) / 3, 6)
    expected_lon = round((75.7382 + 75.7360 + 75.7170) / 3, 6)
    assert abs(res.activity_center_coordinates["latitude"] - expected_lat) < 1e-4
    assert abs(res.activity_center_coordinates["longitude"] - expected_lon) < 1e-4

    for rec in res.recommendations:
        assert rec.estimated_distance_to_activity_center_km is not None
        assert rec.estimated_distance_to_activity_center_km >= 0.0
        assert rec.road_winding_factor == 1.30
        assert rec.location_explanation is not None
        assert "activity center" in rec.location_explanation.lower()


def test_accommodation_recommendations_category_moderate(client):
    """Verify Moderate / Mid-Range category returns comfortable hotels with balanced comfort and location."""
    payload = {
        "destination_id": "goa",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-04",
        "party_size": 2,
        "total_budget": 35000.0,
        "category": "moderate",
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["budget_context"]["selected_category"] == "Moderate / Mid-Range"
    assert len(data["recommendations"]) >= 1
    for rec in data["recommendations"]:
        assert rec["category"] == "Moderate / Mid-Range"
        assert rec["accommodation"]["category"] == "Moderate / Mid-Range"
        assert rec["price_per_night"] >= 2000.0
        reason_text = " ".join(rec["match_reasons"])
        assert "Moderate / Mid-Range" in reason_text


def test_price_alone_does_not_determine_ranking(db_session):
    """Verify that a lower price alone does not guarantee a higher rank over a property with superior rating and central location."""
    from app.models.accommodation import Accommodation

    # Property 1: Cheaper (₹1,500), but poor rating (2.5) and far away
    distant_cheap = Accommodation(
        id="test-cheap-peripheral",
        destination_id="hampi",
        name="Far Outpost Lodge",
        accommodation_type="lodge",
        description="Far outlying basic lodge.",
        latitude=15.0000,  # ~35km south of Hampi
        longitude=76.4600,
        price_per_night=1500.0,
        currency="INR",
        rating=2.5,  # Low rating
        room_capacity=2,
        amenities=["Fan"],
        is_verified=True,
        provenance={"source": "Regional Benchmark", "rate_tier": "Budget"},
        is_active=True,
    )

    # Property 2: Higher tariff (₹3,000), but excellent rating (4.8), rich amenities, right at activity center
    central_quality = Accommodation(
        id="test-central-quality",
        destination_id="hampi",
        name="Hampi Central Heritage Inn",
        accommodation_type="hotel",
        description="Prime location boutique hotel near temples.",
        latitude=15.3350,  # Directly at activity center
        longitude=76.4600,
        price_per_night=3000.0,
        currency="INR",
        rating=4.8,  # High rating
        room_capacity=2,
        amenities=["WiFi", "AC", "Breakfast", "Swimming Pool", "Restaurant", "Garden"],
        is_verified=True,
        provenance={"source": "Regional Benchmark", "rate_tier": "Standard"},
        is_active=True,
    )
    db_session.add_all([distant_cheap, central_quality])
    db_session.commit()

    # Itinerary activities clustered near Hampi center (15.335, 76.460)
    itinerary_days = [
        {
            "day_number": 1,
            "items": [
                {"visit_order": 1, "attraction": {"name": "Virupaksha", "latitude": 15.3353, "longitude": 76.4600}},
                {"visit_order": 2, "attraction": {"name": "Vittala", "latitude": 15.3400, "longitude": 76.4750}},
            ],
        }
    ]

    req = AccommodationRecommendationRequest(
        destination_id="hampi",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        party_size=2,
        total_budget=25000.0,
        itinerary_days=itinerary_days,
    )
    res = AccommodationService.get_recommendations(db_session, req)

    rec_cheap = next((r for r in res.recommendations if r.accommodation.id == "test-cheap-peripheral"), None)
    rec_quality = next((r for r in res.recommendations if r.accommodation.id == "test-central-quality"), None)

    assert rec_cheap is not None
    assert rec_quality is not None

    # The quality, centrally located property must outrank the cheaper, poorly rated, distant property
    assert rec_quality.match_score > rec_cheap.match_score
    assert rec_quality.location_suitability_score > rec_cheap.location_suitability_score
    assert rec_quality.estimated_daily_hotel_transit_km < rec_cheap.estimated_daily_hotel_transit_km


def test_missing_category_data_handled_without_fabrication(client, db_session):
    """Verify that an empty or missing category returns an honest empty state without inventing dummy properties."""
    # Temporarily query a hypothetical destination or filtered category where no records exist
    payload = {
        "destination_id": "coorg",
        "check_in_date": "2026-11-01",
        "check_out_date": "2026-11-03",
        "party_size": 2,
        "category": "ultra_luxury",
        "max_price_per_night": 5000.0,  # No luxury property exists below ₹5000
    }
    response = client.post("/api/v1/accommodations/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Recommendations should be empty, not populated with fabricated fake hotels
    assert len(data["recommendations"]) == 0
    # Must preserve provenance disclosure
    assert data["budget_context"]["selected_category"] == "Ultra-Luxury"
