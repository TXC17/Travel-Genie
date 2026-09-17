"""
Authentication and User Endpoint Integration Tests.
"""

from fastapi import status


def test_register_user_success(client):
    """Test successful user registration and token return."""
    payload = {
        "email": "traveler1@travelgenie.ai",
        "password": "strongpassword123",
        "full_name": "Alice Traveler",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "traveler1@travelgenie.ai"
    assert data["user"]["full_name"] == "Alice Traveler"


def test_register_duplicate_email(client):
    """Test duplicate registration returns 409 conflict."""
    payload = {
        "email": "duplicate@travelgenie.ai",
        "password": "password123",
        "full_name": "Duplicate User",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == status.HTTP_409_CONFLICT


def test_login_success(client):
    """Test user login with valid credentials."""
    reg_payload = {
        "email": "loginuser@travelgenie.ai",
        "password": "correctpassword",
        "full_name": "Login User",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "loginuser@travelgenie.ai",
        "password": "correctpassword",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@travelgenie.ai"


def test_login_invalid_password(client):
    """Test login with incorrect password returns 401."""
    login_payload = {
        "email": "loginuser@travelgenie.ai",
        "password": "wrongpassword",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_profile(client):
    """Test /auth/me returns profile for authenticated user."""
    reg_payload = {
        "email": "meuser@travelgenie.ai",
        "password": "password123",
        "full_name": "Profile User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "meuser@travelgenie.ai"
    assert data["full_name"] == "Profile User"


def test_get_current_user_unauthorized(client):
    """Test /auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
