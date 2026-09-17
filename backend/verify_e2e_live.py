"""
Live End-to-End System Verification against running backend server (http://127.0.0.1:8000).
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api/v1"


def http_req(method: str, path: str, data: dict = None, token: str = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, json.loads(err_body) if err_body else {}


def main():
    print("=================================================================")
    print("TRAVEL GENIE - LIVE SYSTEM VERIFICATION (HTTP: 127.0.0.1:8000)")
    print("=================================================================")

    # 1. Health check
    status, health = http_req("GET", "/health")
    assert status == 200, f"Health check failed: {health}"
    print(f"[PASS] 1. Backend Health Check: status={health.get('status')}, db={health.get('database')}")

    # 2. Register & Login
    email = f"live_verify_{int(urllib.request.time.time())}@travelgenie.ai"
    status, reg_res = http_req(
        "POST",
        "/auth/register",
        {"email": email, "password": "SecurePassword123!", "full_name": "Live Verifier"},
    )
    assert status == 201, f"Registration failed: {reg_res}"
    print(f"[PASS] 2. User Registered: {email}")

    status, login_res = http_req(
        "POST", "/auth/login", {"email": email, "password": "SecurePassword123!"}
    )
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["access_token"]
    print("[PASS] 3. User Login Successful: JWT Bearer Token acquired")

    # 3. Auth Profile Check
    status, profile = http_req("GET", "/auth/me", token=token)
    assert status == 200 and profile["email"] == email, f"Profile failed: {profile}"
    print(f"[PASS] 4. Protected Route Verified: User profile id={profile['id']}")

    # 4. Seasonal Climate Intelligence (Phase 4)
    status, seasonal = http_req("GET", "/recommendations/seasonal-compare?travel_month=11")
    assert status == 200, f"Seasonal comparison failed: {seasonal}"
    top_dest = seasonal["destinations_ranked"][0]["destination_id"]
    print(f"[PASS] 5. Phase 4 Climate Intelligence: Top destination for {seasonal['travel_month_name']} = {top_dest}")

    # 5. End-to-End Programmatic Itinerary Generation (Phase 4 -> 5 -> 6 -> 7 -> 8)
    gen_payload = {
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
    status, gen_res = http_req("POST", "/trips/generate-itinerary", gen_payload, token=token)
    assert status == 201, f"Itinerary generation failed: {gen_res}"
    trip_id = gen_res["trip_id"]
    itin = gen_res["itinerary"]
    diag = gen_res["diagnostics"]

    print(f"[PASS] 6. Programmatic Itinerary Generated: Trip ID = {trip_id}")
    print(f"     - Scheduled Attractions: {itin['total_scheduled_attractions']}")
    print(f"     - Days: {len(itin['days'])}")
    print(f"     - Total Travel Distance: {itin['total_travel_distance_km']} km")
    print(f"     - Distance Reduction %: {itin['aggregate_distance_reduction_pct']}%")
    print(f"     - Total Estimated Cost: INR {itin['total_estimated_cost']}")
    print(f"     - Pipeline Execution Telemetry: {diag['total_duration_ms']} ms across {len(diag['stages'])} stages")

    # 6. Conversational Planning & Smart Replanning (Phase 7)
    status, chat_sess = http_req(
        "POST", "/chat/sessions", {"title": "Hampi Trip Live Chat", "trip_id": trip_id}, token=token
    )
    assert status == 201, f"Chat session creation failed: {chat_sess}"
    session_id = chat_sess["id"]
    print(f"[PASS] 7. Chat Session Created: ID = {session_id}")

    # Prompt 1: Initial request
    prompt1 = "Plan a 3-day Hampi trip for 2 people with 15000 budget, heritage interests, moderate pace and auto."
    status, chat_res1 = http_req(
        "POST", f"/chat/sessions/{session_id}/messages", {"content": prompt1}, token=token
    )
    assert status == 200, f"Chat message 1 failed: {chat_res1}"
    print("[PASS] 8. Conversational Initial Planning Message Processed:")
    preview = chat_res1['content'][:120].encode('ascii', 'ignore').decode('ascii')
    print(f"     - Response preview: {preview}...")

    # Prompt 2: Replanning request
    prompt2 = "Actually, make it 2 days and keep the budget below 12000."
    status, chat_res2 = http_req(
        "POST", f"/chat/sessions/{session_id}/messages", {"content": prompt2}, token=token
    )
    assert status == 200, f"Chat message 2 failed: {chat_res2}"
    assert chat_res2["replanning_diff"] is not None, "Replanning diff missing!"
    diff = chat_res2["replanning_diff"]

    print("[PASS] 9. Smart Replanning Diff Verified:")
    print(f"     - is_replanned: {diff['is_replanned']}")
    print(f"     - Changed constraints: {diff['changed_constraints']}")
    print(f"     - Removed attractions: {[r['name'] for r in diff['removed_attractions']]}")
    print(f"     - Distance change: {diff['distance_change_km']} km")
    print(f"     - Budget change: INR {diff['budget_change']}")

    # 7. Database Persistence & Retrieval
    status, trip_get = http_req("GET", f"/trips/{trip_id}", token=token)
    assert status == 200 and trip_get["id"] == trip_id, f"Trip retrieval failed: {trip_get}"
    print(f"[PASS] 10. Database Persistence Verified: Trip {trip_id} successfully retrieved with itinerary hierarchy")

    print("\n=================================================================")
    print("ALL 10 LIVE SYSTEM INTEGRATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=================================================================")


if __name__ == "__main__":
    main()
