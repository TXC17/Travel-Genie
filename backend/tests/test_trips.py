"""
Trip Management and Preference Endpoint Integration Tests.
"""

from fastapi import status
from app.utils.seed import seed_database


def test_create_and_manage_trip(client, db_session):
    """Test creating a trip with preferences, retrieving it, and updating constraints."""
    seed_database(db_session)

    # 1. Register a user and get auth token
    user_payload = {
        "email": "tripplanner@travelgenie.ai",
        "password": "securepassword",
        "full_name": "Planner Bob",
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a 3-day Coorg trip
    trip_payload = {
        "destination_id": "coorg",
        "title": "Weekend in Misty Coorg",
        "start_date": "2026-10-15",
        "end_date": "2026-10-17",
        "party_size": 2,
        "total_budget": 18000.0,
        "preferences": {
            "interests": ["nature", "culture_religious"],
            "pace": "Moderate",
            "preferred_transport": "auto",
            "max_daily_travel_hours": 3.5,
            "budget_tier": "Standard",
        },
    }
    create_res = client.post("/api/v1/trips", json=trip_payload, headers=headers)
    assert create_res.status_code == status.HTTP_201_CREATED
    trip_data = create_res.json()
    trip_id = trip_data["id"]

    assert trip_data["number_of_days"] == 3
    assert trip_data["total_budget"] == 18000.0
    assert trip_data["preferences"]["pace"] == "Moderate"

    # 3. Retrieve user trips
    list_res = client.get("/api/v1/trips", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) >= 1

    # 4. Retrieve single trip detail
    detail_res = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert detail_res.status_code == status.HTTP_200_OK
    detail_data = detail_res.json()
    assert detail_data["destination"]["id"] == "coorg"
    assert detail_data["destination"]["name"] == "Coorg"

    # 5. Update trip preferences (e.g. increase budget, change pace to Relaxed)
    update_payload = {
        "total_budget": 25000.0,
        "preferences": {
            "interests": ["nature", "adventure"],
            "pace": "Relaxed",
            "preferred_transport": "taxi",
            "max_daily_travel_hours": 2.5,
            "budget_tier": "Luxury",
        },
    }
    update_res = client.put(f"/api/v1/trips/{trip_id}/preferences", json=update_payload, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    updated_data = update_res.json()
    assert updated_data["total_budget"] == 25000.0
    assert updated_data["preferences"]["pace"] == "Relaxed"
    assert updated_data["preferences"]["preferred_transport"] == "taxi"

    # 6. Delete trip
    del_res = client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 7. Verify deletion
    get_del = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert get_del.status_code == status.HTTP_404_NOT_FOUND
