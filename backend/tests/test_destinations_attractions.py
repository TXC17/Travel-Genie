"""
Destinations and Attractions Endpoint Integration Tests.
"""

from fastapi import status
from app.utils.seed import seed_database


def test_get_destinations(client, db_session):
    """Test listing destinations seeded in DB."""
    seed_database(db_session)

    response = client.get("/api/v1/destinations")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 4
    dest_ids = [d["id"] for d in data]
    assert "dandeli" in dest_ids
    assert "hampi" in dest_ids


def test_get_destination_detail_with_seasonal(client, db_session):
    """Test getting single destination with 12-month climate records."""
    seed_database(db_session)

    response = client.get("/api/v1/destinations/hampi")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "hampi"
    assert len(data["seasonal_records"]) == 12
    assert data["attractions_count"] == 10


def test_get_attraction_categories(client, db_session):
    """Test listing attraction categories."""
    seed_database(db_session)

    response = client.get("/api/v1/attractions/categories")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
    cat_ids = [c["id"] for c in data]
    assert "adventure" in cat_ids
    assert "heritage" in cat_ids


def test_filter_attractions_by_destination_and_category(client, db_session):
    """Test filtering attractions by destination and category."""
    seed_database(db_session)

    # Filter Dandeli adventure attractions
    response = client.get("/api/v1/attractions?destination_id=dandeli&category=adventure")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    for a in data:
        assert a["destination_id"] == "dandeli"
        assert a["category"] == "adventure"
        assert a["is_verified"] is True
        assert "coordinates_source" in a["provenance"]
