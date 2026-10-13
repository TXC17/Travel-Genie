"""
Phase 8 End-to-End Pipeline, Diagnostics, and Observability Integration Tests.
"""

import pytest
from fastapi import status
from app.utils.seed import seed_database
from app.services.pipeline_service import PlanningPipelineService


@pytest.fixture
def auth_headers(client, db_session):
    """Fixture providing valid authentication headers."""
    seed_database(db_session)
    user_payload = {
        "email": "pipeline_tester@travelgenie.ai",
        "password": "SecurePassword123!",
        "full_name": "Pipeline Tester",
    }
    client.post("/api/v1/auth/register", json=user_payload)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "pipeline_tester@travelgenie.ai", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_programmatic_generate_itinerary(client, auth_headers):
    """
    Test programmatic pipeline generation (MCDM -> K-Means -> OR-Tools -> Persistence -> Diagnostics).
    """
    payload = {
        "destination_id": "hampi",
        "duration_days": 3,
        "total_budget": 15000.0,
        "party_size": 2,
        "interests": ["heritage"],
        "pace": "Moderate",
        "preferred_transport": "auto",
        "travel_month": 11,
        "start_date": "2026-11-01",
    }

    res = client.post("/api/v1/trips/generate-itinerary", json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert data["destination_id"] == "hampi"
    assert data["trip_id"] is not None
    assert data["itinerary_id"] is not None
    assert data["itinerary"]["total_days"] == 3
    assert data["itinerary"]["total_scheduled_attractions"] > 0
    assert len(data["itinerary"]["days"]) == 3

    # Verify Diagnostics and Telemetry
    diag = data["diagnostics"]
    assert diag["status"] == "COMPLETED"
    assert diag["total_duration_ms"] > 0.0
    assert diag["recommended_attractions_count"] > 0
    assert diag["clusters_count"] == 3
    assert len(diag["stages"]) == 5  # MCDM, Clustering, Optimization, Persistence, NLG

    stage_names = [s["stage_name"] for s in diag["stages"]]
    assert "MCDM_RECOMMENDATION" in stage_names
    assert "SPATIAL_CLUSTERING" in stage_names
    assert "ROUTE_OPTIMIZATION_AND_SCHEDULING" in stage_names
    assert "DATABASE_PERSISTENCE" in stage_names
    assert "NLG_EXPLANATION" in stage_names

    # Verify Explanation summary
    assert "Hampi" in data["explanation"]
    assert "Optimized Itinerary" in data["explanation"]


def test_pipeline_invalid_destination_error(client, auth_headers):
    """Verify structured 404 error returned when destination is non-existent."""
    payload = {
        "destination_id": "non_existent_city",
        "duration_days": 2,
        "total_budget": 10000.0,
        "party_size": 1,
        "interests": ["heritage"],
        "pace": "Moderate",
        "preferred_transport": "auto",
        "travel_month": 11,
        "start_date": "2026-11-01",
    }

    res = client.post("/api/v1/trips/generate-itinerary", json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in res.json()["detail"].lower()


def test_pipeline_unauthorized_access(client):
    """Verify unauthenticated requests are rejected with 401 and explicit Bearer token error message."""
    payload = {
        "destination_id": "hampi",
        "duration_days": 2,
    }
    res = client.post("/api/v1/trips/generate-itinerary", json=payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Not authenticated. Bearer token required."


# -----------------------------------------------------------------------------
# AUDIT-04: Persisted Trip End Date Regression Tests
# -----------------------------------------------------------------------------

def test_calculate_persisted_end_date_unit():
    """Verify inclusive end date calculation across one-day, multi-day, month-spanning, and year-spanning trips."""
    calc = PlanningPipelineService.calculate_persisted_end_date

    # 1. One-day trip: start_date == end_date
    assert calc("2026-10-20", 1) == "2026-10-20"
    assert calc("2026-01-01", 1) == "2026-01-01"

    # 2. Multi-day trip within same month
    assert calc("2026-10-20", 5) == "2026-10-24"
    assert calc("2026-11-01", 3) == "2026-11-03"

    # 3. Trip spanning end of month
    assert calc("2026-10-30", 3) == "2026-11-01"
    assert calc("2026-02-27", 4) == "2026-03-02"  # February non-leap year

    # 4. Trip spanning end of year
    assert calc("2026-12-30", 4) == "2027-01-02"
    assert calc("2026-12-31", 2) == "2027-01-01"


def test_pipeline_persists_correct_inclusive_end_dates_e2e(client, auth_headers):
    """
    Verify end-to-end itinerary generation persists the correct inclusive end_date
    in the database for both one-day and multi-day trips.
    """
    # 1. Multi-day trip spanning month boundary (Oct 30 to Nov 1 = 3 days)
    payload_multiday = {
        "destination_id": "hampi",
        "duration_days": 3,
        "total_budget": 15000.0,
        "party_size": 2,
        "interests": ["heritage"],
        "pace": "Moderate",
        "preferred_transport": "auto",
        "travel_month": 10,
        "start_date": "2026-10-30",
    }
    res = client.post("/api/v1/trips/generate-itinerary", json=payload_multiday, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    trip_id = data["trip_id"]

    # Verify persisted trip record via API
    trip_res = client.get(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert trip_res.status_code == status.HTTP_200_OK
    trip_data = trip_res.json()
    assert trip_data["start_date"] == "2026-10-30"
    assert trip_data["end_date"] == "2026-11-01"
    assert trip_data["number_of_days"] == 3

    # 2. One-day trip (start_date == end_date)
    payload_oneday = {
        "destination_id": "hampi",
        "duration_days": 1,
        "total_budget": 5000.0,
        "party_size": 1,
        "interests": ["heritage"],
        "pace": "Moderate",
        "preferred_transport": "auto",
        "travel_month": 11,
        "start_date": "2026-11-15",
    }
    res_one = client.post("/api/v1/trips/generate-itinerary", json=payload_oneday, headers=auth_headers)
    assert res_one.status_code == status.HTTP_201_CREATED
    data_one = res_one.json()
    trip_one_id = data_one["trip_id"]

    trip_one_res = client.get(f"/api/v1/trips/{trip_one_id}", headers=auth_headers)
    assert trip_one_res.status_code == status.HTTP_200_OK
    trip_one_data = trip_one_res.json()
    assert trip_one_data["start_date"] == "2026-11-15"
    assert trip_one_data["end_date"] == "2026-11-15"
    assert trip_one_data["number_of_days"] == 1

    # 3. Year-spanning trip (Dec 30 to Jan 1 = 3 days)
    payload_year = {
        "destination_id": "hampi",
        "duration_days": 3,
        "total_budget": 15000.0,
        "party_size": 1,
        "interests": ["heritage"],
        "pace": "Moderate",
        "preferred_transport": "auto",
        "travel_month": 12,
        "start_date": "2026-12-30",
    }
    res_year = client.post("/api/v1/trips/generate-itinerary", json=payload_year, headers=auth_headers)
    assert res_year.status_code == status.HTTP_201_CREATED
    data_year = res_year.json()
    trip_year_id = data_year["trip_id"]

    trip_year_res = client.get(f"/api/v1/trips/{trip_year_id}", headers=auth_headers)
    assert trip_year_res.status_code == status.HTTP_200_OK
    trip_year_data = trip_year_res.json()
    assert trip_year_data["start_date"] == "2026-12-30"
    assert trip_year_data["end_date"] == "2027-01-01"
    assert trip_year_data["number_of_days"] == 3


def test_pipeline_rejects_invalid_start_date(client, auth_headers):
    """Verify validation error when start_date is not in ISO YYYY-MM-DD format."""
    payload = {
        "destination_id": "hampi",
        "duration_days": 2,
        "start_date": "invalid-date",
    }
    res = client.post("/api/v1/trips/generate-itinerary", json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
