"""
Unit and Integration Tests for Conversational AI, Constraint Extraction, and Smart Replanning.
Validates natural language understanding, clarification logic, deterministic pipeline orchestration,
itinerary persistence, and smart replanning diffs.
"""

import pytest
from fastapi import status
from app.algorithms.conversation import ConversationalEngine
from app.utils.seed import seed_database


def test_rule_based_constraint_extraction_full():
    """Verify regex/rule-based NLU extracts all explicit travel constraints."""
    engine = ConversationalEngine()
    prompt = (
        "Plan a 3-day Hampi trip for 2 people with a ₹15,000 budget. "
        "I like heritage and ancient temples, and prefer a moderate pace with an auto."
    )

    constraints = engine.extract_constraints(prompt)

    assert constraints.destination_id == "hampi"
    assert constraints.duration_days == 3
    assert constraints.party_size == 2
    assert constraints.total_budget == 15000.0
    assert "heritage" in constraints.interests
    assert constraints.pace == "Moderate"
    assert constraints.preferred_transport == "auto"
    assert constraints.is_complete is True
    assert len(constraints.missing_fields) == 0


def test_constraint_extraction_clarification_on_missing_destination():
    """Verify clarification question is triggered when destination is missing."""
    engine = ConversationalEngine()
    prompt = "I want a 3-day trip for 2 people with a 15k budget."

    constraints = engine.extract_constraints(prompt)

    assert constraints.destination_id is None
    assert constraints.duration_days == 3
    assert constraints.is_complete is False
    assert "destination" in constraints.missing_fields
    assert constraints.clarification_question is not None
    assert "Hampi" in constraints.clarification_question


def test_constraint_extraction_clarification_on_missing_duration():
    """Verify clarification question is triggered when duration is missing."""
    engine = ConversationalEngine()
    prompt = "I want to visit Coorg to see coffee plantations and waterfalls."

    constraints = engine.extract_constraints(prompt)

    assert constraints.destination_id == "coorg"
    assert constraints.duration_days is None
    assert constraints.is_complete is False
    assert "duration_days" in constraints.missing_fields
    assert constraints.clarification_question is not None


def test_contextual_constraint_merging_across_turns():
    """Verify follow-up message merges seamlessly with previous constraints."""
    engine = ConversationalEngine()
    turn1_prompt = "Plan a 3-day Hampi trip with a ₹15,000 budget."
    turn1_constraints = engine.extract_constraints(turn1_prompt)

    # User modifies duration in turn 2
    turn2_prompt = "Actually make it 2 days."
    turn2_constraints = engine.extract_constraints(turn2_prompt, previous_constraints=turn1_constraints)

    assert turn2_constraints.destination_id == "hampi"  # Preserved from turn 1
    assert turn2_constraints.duration_days == 2         # Updated from turn 2
    assert turn2_constraints.total_budget == 15000.0   # Preserved from turn 1
    assert turn2_constraints.is_complete is True


@pytest.fixture
def auth_headers(client, db_session):
    """Fixture providing valid authentication headers."""
    seed_database(db_session)
    user_payload = {
        "email": "chatuser@travelgenie.ai",
        "password": "SecurePassword123!",
        "full_name": "Chat Alice",
    }
    client.post("/api/v1/auth/register", json=user_payload)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "chatuser@travelgenie.ai", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_session_lifecycle(client, auth_headers):
    """Test creating, listing, and retrieving chat sessions for authenticated user."""
    # 1. Create Session
    create_res = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Hampi Heritage Trip"},
        headers=auth_headers,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Hampi Heritage Trip"

    # 2. List Sessions
    list_res = client.get("/api/v1/chat/sessions", headers=auth_headers)
    assert list_res.status_code == status.HTTP_200_OK
    sessions = list_res.json()
    assert any(s["id"] == session_id for s in sessions)

    # 3. Get Session Detail
    get_res = client.get(f"/api/v1/chat/sessions/{session_id}", headers=auth_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == session_id


def test_chat_session_unauthorized_access(client, auth_headers):
    """Verify user cannot access another user's chat session."""
    # 1. Create session as user 1
    create_res = client.post(
        "/api/v1/chat/sessions",
        json={"title": "User 1 Chat"},
        headers=auth_headers,
    )
    session_id = create_res.json()["id"]

    # 2. Register user 2
    client.post(
        "/api/v1/auth/register",
        json={"email": "other_user@example.com", "password": "SecurePassword123!", "full_name": "Other User"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "other_user@example.com", "password": "SecurePassword123!"},
    )
    user2_token = login_res.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # 3. User 2 attempts to read User 1's session -> Must be 403 Forbidden
    unauthorized_res = client.get(f"/api/v1/chat/sessions/{session_id}", headers=user2_headers)
    assert unauthorized_res.status_code == status.HTTP_403_FORBIDDEN


def test_end_to_end_conversational_planning_and_smart_replanning(client, auth_headers, db_session):
    """
    Complete End-to-End Acceptance Test:
    Turn 1: Natural Language Prompt -> NLU -> MCDM -> K-Means -> OR-Tools -> Persisted Itinerary -> Explanation.
    Turn 2: Replanning Request ("Make it 2 days") -> Constraint Diff -> Re-optimization -> Updated Itinerary.
    """
    seed_database(db_session)

    # 1. Create Session
    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"title": "End-to-End Hampi Planning"},
        headers=auth_headers,
    )
    session_id = session_res.json()["id"]

    # 2. Turn 1: Initial Planning Prompt
    turn1_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "content": "Plan a 3-day Hampi trip for 2 people with a ₹15,000 budget. I like heritage places and prefer a moderate pace with an auto."
        },
        headers=auth_headers,
    )
    assert turn1_res.status_code == status.HTTP_200_OK
    turn1_data = turn1_res.json()

    assert turn1_data["is_clarification"] is False
    assert turn1_data["extracted_constraints"]["destination_id"] == "hampi"
    assert turn1_data["extracted_constraints"]["duration_days"] == 3
    assert turn1_data["itinerary"] is not None
    assert turn1_data["itinerary"]["total_days"] == 3
    assert turn1_data["persisted_itinerary_id"] is not None
    assert "Hampi" in turn1_data["content"]
    assert "Distance Reduction" in turn1_data["content"] or "reduction" in turn1_data["content"].lower()

    # 3. Turn 2: Smart Replanning ("Actually make it 2 days and keep budget under ₹12,000")
    turn2_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Actually, make it 2 days and keep the budget below ₹12,000."},
        headers=auth_headers,
    )
    assert turn2_res.status_code == status.HTTP_200_OK
    turn2_data = turn2_res.json()

    assert turn2_data["is_clarification"] is False
    assert turn2_data["extracted_constraints"]["duration_days"] == 2
    assert turn2_data["extracted_constraints"]["total_budget"] == 12000.0
    assert turn2_data["itinerary"]["total_days"] == 2

    # Verify Replanning Diff
    diff = turn2_data["replanning_diff"]
    assert diff is not None
    assert diff["is_replanned"] is True
    assert any(c["field"] == "duration_days" and c["old_value"] == 3 and c["new_value"] == 2 for c in diff["changed_constraints"])
    assert "Smart Replanning" in turn2_data["content"]


def test_conversational_clarification_flow(client, auth_headers):
    """Verify that underspecified prompts return a polite clarification response."""
    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Vague Planning"},
        headers=auth_headers,
    )
    session_id = session_res.json()["id"]

    msg_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "I want to go on vacation with my friends."},
        headers=auth_headers,
    )
    assert msg_res.status_code == status.HTTP_200_OK
    data = msg_res.json()

    assert data["is_clarification"] is True
    assert data["itinerary"] is None
    assert "Which destination" in data["content"]


def test_extraction_various_interests_and_transports():
    """Verify parser extracts adventure, nature, rafting, rental bike, and family size."""
    engine = ConversationalEngine()
    prompt = (
        "We are a family of 4 planning a 2-day Dandeli trip with ₹20,000 budget. "
        "We want adventure, river rafting, and camping with a rental vehicle at an intense pace."
    )
    constraints = engine.extract_constraints(prompt)

    assert constraints.destination_id == "dandeli"
    assert constraints.duration_days == 2
    assert constraints.party_size == 4
    assert constraints.total_budget == 20000.0
    assert "adventure" in constraints.interests
    assert constraints.preferred_transport == "rental"
    assert constraints.pace == "Intense"
    assert constraints.is_complete is True


def test_smart_replanning_transport_and_pace_change(client, auth_headers, db_session):
    """Verify smart replanning when user switches transport and pace."""
    seed_database(db_session)

    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Coorg Trip Replanning"},
        headers=auth_headers,
    )
    session_id = session_res.json()["id"]

    # Turn 1
    t1_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Plan a 2-day Coorg trip with an auto at a Moderate pace."},
        headers=auth_headers,
    )
    assert t1_res.status_code == status.HTTP_200_OK
    t1_data = t1_res.json()
    assert t1_data["extracted_constraints"]["preferred_transport"] == "auto"

    # Turn 2: Switch to car and Relaxed pace
    t2_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Switch to a taxi and make the pace Relaxed."},
        headers=auth_headers,
    )
    assert t2_res.status_code == status.HTTP_200_OK
    t2_data = t2_res.json()
    assert t2_data["extracted_constraints"]["preferred_transport"] == "car"
    assert t2_data["extracted_constraints"]["pace"] == "Relaxed"
    assert t2_data["replanning_diff"]["is_replanned"] is True
    changed_fields = [c["field"] for c in t2_data["replanning_diff"]["changed_constraints"]]
    assert "preferred_transport" in changed_fields or "pace" in changed_fields
