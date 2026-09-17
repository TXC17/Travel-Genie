"""
Phase 8 End-to-End Pipeline, Diagnostics, and Observability Integration Tests.
"""

import pytest
from fastapi import status
from app.utils.seed import seed_database


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
    """Verify unauthenticated requests are rejected with 401."""
    payload = {
        "destination_id": "hampi",
        "duration_days": 2,
    }
    res = client.post("/api/v1/trips/generate-itinerary", json=payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
