"""
Health check and root API endpoint tests.
"""

from fastapi import status


def test_root_endpoint(client):
    """Test root redirection and metadata payload."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "online"
    assert "Travel Genie" in data["project"]
    assert data["api_v1"] == "/api/v1"


def test_health_check_endpoint(client):
    """Test health check route returns healthy status with db connection."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data
