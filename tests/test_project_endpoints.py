from fastapi.testclient import TestClient

from backend.app.api import project_endpoints
from backend.app.main import create_app
from backend.app.models.org_memory import clear_org_memory


def _client() -> TestClient:
    clear_org_memory()
    with project_endpoints._STATE_LOCK:
        project_endpoints.MEETING_STATES.clear()
    return TestClient(create_app())


def test_meeting_approval_is_immutable() -> None:
    client = _client()

    first = client.post(
        "/projects/proj-1/meetings/m-1/review",
        json={"action": "approve"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "approved"
    assert first.json()["locked"] is True

    second = client.post(
        "/projects/proj-1/meetings/m-1/review",
        json={"action": "deny"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "approved"
    assert second.json()["locked"] is True
    assert "immutable" in second.json()["message"].lower()


def test_approved_meeting_populates_decision_evolution() -> None:
    client = _client()

    initial = client.get("/projects/proj-1/decisions")
    assert initial.status_code == 200
    assert initial.json()["decisions"] == []

    review = client.post(
        "/projects/proj-1/meetings/m-1/review",
        json={"action": "approve"},
    )
    assert review.status_code == 200

    decisions = client.get("/projects/proj-1/decisions")
    assert decisions.status_code == 200
    payload = decisions.json()
    assert len(payload["decisions"]) == 1
    assert payload["decisions"][0]["decision_id"] == "dec-1"
    assert payload["decisions"][0]["latest_version"] == "v1"
    assert payload["decisions"][0]["versions"][0]["stakeholders"]


def test_non_attendees_are_marked_as_drifting_in_alignment() -> None:
    client = _client()

    approve_first = client.post(
        "/projects/proj-1/meetings/m-1/review",
        json={"action": "approve"},
    )
    assert approve_first.status_code == 200

    approve_second = client.post(
        "/projects/proj-1/meetings/m-2/review",
        json={"action": "approve"},
    )
    assert approve_second.status_code == 200

    decisions = client.get("/projects/proj-1/decisions")
    assert decisions.status_code == 200
    decision_payload = decisions.json()["decisions"][0]
    assert decision_payload["latest_version"] == "v2"
    assert decision_payload["status"] == "drifting"

    alignment = client.get("/projects/proj-1/alignment")
    assert alignment.status_code == 200
    alignment_payload = alignment.json()
    assert alignment_payload["alignment_status"] == "drift_detected"
    assert "product" in alignment_payload["out_of_sync_departments"]

    product_dept = next(
        department
        for department in alignment_payload["departments"]
        if department["department_id"] == "product"
    )
    assert product_dept["status"] == "drifting"
    assert any(item["status"] == "out_of_sync" for item in product_dept["stakeholders"])


def test_q1_roadmap_sync_approval_adds_second_decision_card() -> None:
    client = _client()

    review = client.post(
        "/projects/proj-1/meetings/m-3/review",
        json={"action": "approve"},
    )
    assert review.status_code == 200

    decisions = client.get("/projects/proj-1/decisions")
    assert decisions.status_code == 200
    payload = decisions.json()

    decision_ids = {item["decision_id"] for item in payload["decisions"]}
    assert "dec-2" in decision_ids
    assert "dec-6" in decision_ids
    assert len(payload["decisions"]) == 2


def test_team_acceptance_updates_alignment_and_notifies_downstream() -> None:
    client = _client()

    approve_first = client.post("/projects/proj-1/meetings/m-1/review", json={"action": "approve"})
    assert approve_first.status_code == 200
    approve_second = client.post("/projects/proj-1/meetings/m-2/review", json={"action": "approve"})
    assert approve_second.status_code == 200

    pre_alignment = client.get("/projects/proj-1/alignment")
    assert pre_alignment.status_code == 200
    assert pre_alignment.json()["alignment_status"] == "drift_detected"

    reports_response = client.get("/projects/proj-1/stakeholders/s-1/reports")
    assert reports_response.status_code == 200
    reports = reports_response.json()["reports"]
    report_ids = {item["stakeholder_id"] for item in reports}
    assert {"s-13", "s-14", "s-15", "s-16"}.issubset(report_ids)

    accept_response = client.post(
        "/projects/proj-1/stakeholders/s-1/accept-latest",
        json={"include_downstream": True},
    )
    assert accept_response.status_code == 200
    accept_payload = accept_response.json()
    notified_ids = {item["stakeholder_id"] for item in accept_payload["notified_stakeholders"]}
    assert "s-1" in notified_ids
    assert {"s-13", "s-14", "s-15", "s-16"}.issubset(notified_ids)

    post_alignment = client.get("/projects/proj-1/alignment")
    assert post_alignment.status_code == 200
    assert post_alignment.json()["alignment_status"] == "aligned"
