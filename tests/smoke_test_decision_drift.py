from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.decision_graph import (
    add_decision,
    add_decision_version,
    add_stakeholder,
    init_graph,
    link_supersedes,
    record_reference,
)
from backend.app.core.drift_detection import detect_decision_drift
from backend.app.core.explanation_generator import generate_drift_explanation
from backend.app.core.semantic_change import classify_decision_change
from backend.app.core.version_resolution import get_latest_decision_version


def run_smoke_test() -> None:
    print("=== Decision Drift Smoke Test ===")
    graph = init_graph()

    add_decision(graph, decision_id="dec-1", title="Analytics datastore")
    add_decision_version(
        graph,
        version_id="v1",
        decision_id="dec-1",
        content="Use Postgres for analytics MVP",
        confidence=0.9,
        reasoning="Fast to ship with existing team skills",
    )
    add_decision_version(
        graph,
        version_id="v2",
        decision_id="dec-1",
        content="Use BigQuery for analytics due to scale",
        confidence=0.8,
        reasoning="Projected load is higher than expected",
    )
    link_supersedes(graph, new_version_id="v2", previous_version_id="v1")

    add_stakeholder(graph, stakeholder_id="s1", name="Alice", role="Product")
    add_stakeholder(graph, stakeholder_id="s2", name="Bob", role="Infra")
    record_reference(graph, version_id="v1", stakeholder_id="s1")
    record_reference(graph, version_id="v2", stakeholder_id="s2")

    latest = get_latest_decision_version(graph, "dec-1")
    print(f"[latest_version] {latest}")
    assert latest == "decision_version:v2", f"Expected latest v2, got {latest}"

    drift = detect_decision_drift(graph, "dec-1")
    print(f"[drift_detection] {drift}")
    assert drift["decision_id"] == "dec-1"
    assert drift["drift_detected"] is True
    assert set(drift["referenced_versions"]) == {"v1", "v2"}
    assert drift["stakeholder_versions"].get("s1") == ["v1"]
    assert drift["stakeholder_versions"].get("s2") == ["v2"]

    explanation = generate_drift_explanation(graph, "dec-1")
    print(f"[drift_explanation] {explanation}")
    assert explanation["decision_id"] == "dec-1"
    assert explanation["drift_detected"] is True
    assert explanation["latest_version"] == "v2"
    assert "s1" in explanation["out_of_sync_stakeholders"]
    assert isinstance(explanation["explanation"], str) and explanation["explanation"].strip()

    change = classify_decision_change(
        previous_content="Use Postgres for analytics MVP",
        new_content="Use BigQuery for analytics due to scale",
    )
    print(f"[semantic_change] {change}")
    assert set(change.keys()) == {"change_type", "explanation"}
    assert change["change_type"] in {"no_change", "minor_change", "major_change"}
    assert isinstance(change["explanation"], str) and change["explanation"].strip()

    print("PASS: decision drift smoke test")


if __name__ == "__main__":
    run_smoke_test()
