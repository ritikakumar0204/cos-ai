from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.models.org_memory import clear_org_memory


def _client() -> TestClient:
    clear_org_memory()
    return TestClient(create_app())


def test_mcp_lists_tools() -> None:
    client = _client()
    response = client.get("/mcp/tools")
    assert response.status_code == 200

    tool_names = {tool["name"] for tool in response.json()}
    assert "process_meeting_update" in tool_names
    assert "stamp_decision_and_route" in tool_names
    assert "what_changed_today" in tool_names
    assert "add_stakeholder_context" in tool_names
    assert "detect_conflicts_for_review" in tool_names


def test_scenario_meeting_ended_updates_graph() -> None:
    client = _client()
    response = client.post(
        "/mcp/scenarios/meeting-ended",
        json={
            "project_id": "proj-42",
            "meeting_id": "mtg-42",
            "title": "Weekly sync",
            "summary": "Finalized API contract.",
            "participants": [
                {
                    "stakeholder_id": "s-1",
                    "name": "Alice",
                    "department": "Product",
                    "role": "Owner",
                }
            ],
            "decisions": [
                {
                    "decision_id": "dec-42",
                    "title": "API shape",
                    "version_id": "v1",
                    "content": "Ship /query v1.",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["project_id"] == "proj-42"
    assert payload["result"]["updated_decisions"][0]["decision_id"] == "dec-42"


def test_scenario_decision_made_routes_targets() -> None:
    client = _client()
    response = client.post(
        "/mcp/scenarios/decision-made",
        json={
            "project_id": "proj-99",
            "decision_id": "dec-1",
            "title": "Datastore choice",
            "version_id": "v2",
            "content": "Use BigQuery.",
            "stakeholders": [
                {
                    "stakeholder_id": "s-1",
                    "name": "Alice",
                    "department": "Product",
                    "role": "Owner",
                },
                {
                    "stakeholder_id": "s-2",
                    "name": "Bob",
                    "department": "Engineering",
                    "role": "Contributor",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["latest_version"] == "v2"
    assert "routing" in payload["result"]


def test_scenario_what_changed_today_returns_map() -> None:
    client = _client()
    # Seed one event first so timeline is non-empty.
    stamp = client.post(
        "/mcp/scenarios/decision-made",
        json={
            "project_id": "proj-8",
            "decision_id": "dec-8",
            "title": "Security policy",
            "version_id": "v1",
            "content": "Enforce MFA.",
            "stakeholders": [],
        },
    )
    assert stamp.status_code == 200

    response = client.post(
        "/mcp/scenarios/what-changed-today",
        json={"project_id": "proj-8"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["project_id"] == "proj-8"
    assert "visual_map" in payload["result"]


def test_scenario_stakeholder_joined_returns_context() -> None:
    client = _client()
    response = client.post(
        "/mcp/scenarios/stakeholder-joined",
        json={
            "project_id": "proj-5",
            "stakeholder_id": "s-55",
            "name": "Riya",
            "department": "Operations",
            "role": "Informed",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["context"]["exists"] is True
    assert payload["result"]["context"]["stakeholder_id"] == "s-55"


def test_scenario_conflict_scan_detects_drift() -> None:
    client = _client()

    # Create decision with two versions and references to different versions.
    first = client.post(
        "/mcp/scenarios/decision-made",
        json={
            "project_id": "proj-7",
            "decision_id": "dec-7",
            "title": "Queue strategy",
            "version_id": "v1",
            "content": "Use Redis queue.",
            "stakeholders": [
                {
                    "stakeholder_id": "s-1",
                    "name": "Alice",
                    "department": "Product",
                    "role": "Owner",
                }
            ],
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/mcp/scenarios/decision-made",
        json={
            "project_id": "proj-7",
            "decision_id": "dec-7",
            "title": "Queue strategy",
            "version_id": "v2",
            "content": "Use managed Kafka.",
            "stakeholders": [
                {
                    "stakeholder_id": "s-2",
                    "name": "Bob",
                    "department": "Engineering",
                    "role": "Contributor",
                }
            ],
        },
    )
    assert second.status_code == 200

    response = client.post("/mcp/scenarios/scan-conflicts", json={"project_id": "proj-7"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["project_id"] == "proj-7"
    assert "findings" in payload["result"]
