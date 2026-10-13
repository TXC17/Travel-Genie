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
