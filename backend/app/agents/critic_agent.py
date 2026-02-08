from __future__ import annotations

from typing import Any

from ..core.drift_detection import detect_decision_drift
from ..core.version_resolution import get_latest_decision_version
from ..models.org_memory import get_project_graph, record_event


class CriticAgent:
    """Critic agent that flags contradictory or drifting organizational signals."""

    @staticmethod
    def _project_decisions(graph, project_id: str) -> list[str]:
        decisions: list[str] = []
        for node_id, attrs in graph.nodes(data=True):
            if attrs.get("type") != "decision":
                continue
            if attrs.get("project_id") == project_id:
                decisions.append(node_id)
        return decisions

    def detect_conflicts(self, project_id: str) -> dict[str, Any]:
        """Evaluate a project graph and flag decisions with conflicting signals."""
        graph = get_project_graph(project_id)
        decision_nodes = self._project_decisions(graph, project_id)

        findings: list[dict[str, Any]] = []

        for decision_node in decision_nodes:
            decision_id = graph.nodes[decision_node].get("decision_id")
            if not decision_id:
                continue

            try:
                _ = get_latest_decision_version(graph, decision_id)
            except ValueError as exc:
                findings.append(
                    {
                        "decision_id": decision_id,
                        "severity": "high",
                        "issue": "version_lineage_conflict",
                        "detail": str(exc),
                    }
                )

            drift = detect_decision_drift(graph, decision_id)
            if bool(drift.get("drift_detected")):
                findings.append(
                    {
                        "decision_id": decision_id,
                        "severity": "medium",
                        "issue": "alignment_drift",
                        "detail": (
                            "Stakeholders are referencing different versions: "
                            f"{', '.join(drift.get('referenced_versions', []))}"
                        ),
                        "stakeholder_versions": drift.get("stakeholder_versions", {}),
                    }
                )

        event = record_event(
            project_id,
            "critic_review",
            {
                "conflict_count": len(findings),
            },
        )

        return {
            "project_id": project_id,
            "conflicts_detected": len(findings) > 0,
            "conflict_count": len(findings),
            "findings": findings,
            "event": event,
        }
