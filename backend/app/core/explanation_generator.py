import networkx as nx

from .drift_detection import detect_decision_drift
from .version_resolution import get_latest_decision_version


def _version_label_from_node_id(version_node_id: str) -> str:
    if version_node_id.startswith("decision_version:"):
        return version_node_id.split("decision_version:", 1)[1]
    return version_node_id


def _stakeholder_role_index(graph: nx.DiGraph) -> dict[str, str]:
    role_index: dict[str, str] = {}
    for _, attrs in graph.nodes(data=True):
        if attrs.get("type") != "stakeholder":
            continue
        stakeholder_id = attrs.get("stakeholder_id")
        if not stakeholder_id:
            continue
        role = attrs.get("role")
        if isinstance(role, str):
            role_index[stakeholder_id] = role
    return role_index


def _format_role_segment(
    label: str, stakeholder_ids: list[str], referenced_versions: dict[str, list[str]]
) -> str | None:
    if not stakeholder_ids:
        return None
    details: list[str] = []
    for stakeholder_id in sorted(stakeholder_ids):
        versions = referenced_versions.get(stakeholder_id, [])
        refs = ", ".join(sorted(versions)) if versions else "none"
        details.append(f"{stakeholder_id} ({refs})")
    return f"{label}: {', '.join(details)}"


def generate_drift_explanation(graph: nx.DiGraph, decision_id: str) -> dict:
    latest_version_node: str | None = None
    latest_version_label: str | None = None

    try:
        latest_version_node = get_latest_decision_version(graph, decision_id)
        latest_version_label = _version_label_from_node_id(latest_version_node)
    except ValueError:
        drift_info = detect_decision_drift(graph, decision_id)
        return {
            "decision_id": decision_id,
            "drift_detected": bool(drift_info.get("drift_detected", False)),
            "latest_version": None,
            "out_of_sync_stakeholders": [],
            "explanation": "Latest version could not be resolved for this decision.",
        }

    drift_info = detect_decision_drift(graph, decision_id)
    stakeholder_versions: dict[str, list[str]] = drift_info.get("stakeholder_versions", {})
    stakeholder_roles = _stakeholder_role_index(graph)

    out_of_sync_stakeholders: list[str] = []
    out_of_sync_details: list[str] = []
    aligned_by_role: dict[str, list[str]] = {}
    out_of_sync_by_role: dict[str, list[str]] = {}
    for stakeholder_id, versions in stakeholder_versions.items():
        role = stakeholder_roles.get(stakeholder_id, "Unknown")
        if latest_version_label not in versions:
            out_of_sync_stakeholders.append(stakeholder_id)
            referenced = ", ".join(sorted(versions)) if versions else "none"
            out_of_sync_details.append(f"{stakeholder_id} references {referenced}")
            out_of_sync_by_role.setdefault(role, []).append(stakeholder_id)
        else:
            aligned_by_role.setdefault(role, []).append(stakeholder_id)

    drift_detected = len(out_of_sync_stakeholders) > 0

    if not drift_detected:
        critical_aligned = sorted(aligned_by_role.get("Owner", [])) + sorted(
            aligned_by_role.get("Contributor", [])
        )
        secondary_aligned = sorted(aligned_by_role.get("Informed", [])) + sorted(
            aligned_by_role.get("Affected", [])
        )
        if critical_aligned or secondary_aligned:
            clauses: list[str] = []
            if critical_aligned:
                clauses.append(
                    f"Owners and Contributors aligned: {', '.join(sorted(critical_aligned))}"
                )
            if secondary_aligned:
                clauses.append(
                    f"Informed and Affected aligned: {', '.join(sorted(secondary_aligned))}"
                )
            explanation = (
                f"All referencing stakeholders are aligned on the latest version "
                f"{latest_version_label}. {'; '.join(clauses)}."
            )
        else:
            explanation = (
                f"All referencing stakeholders are aligned on the latest version "
                f"{latest_version_label}."
            )
    else:
        latest_created_at = graph.nodes[latest_version_node].get("created_at")
        when_clause = (
            f" after version {latest_version_label} was created at {latest_created_at}"
            if latest_created_at
            else f" after version {latest_version_label} was introduced"
        )

        owners_out = sorted(out_of_sync_by_role.get("Owner", []))
        contributors_out = sorted(out_of_sync_by_role.get("Contributor", []))
        informed_out = sorted(out_of_sync_by_role.get("Informed", []))
        affected_out = sorted(out_of_sync_by_role.get("Affected", []))
        observers_out = sorted(out_of_sync_by_role.get("Observer", []))

        owners_aligned = sorted(aligned_by_role.get("Owner", []))
        contributors_aligned = sorted(aligned_by_role.get("Contributor", []))

        role_segments: list[str] = []
        primary_out_segment = _format_role_segment(
            "Owner/Contributor out-of-sync",
            sorted(owners_out + contributors_out),
            stakeholder_versions,
        )
        if primary_out_segment:
            role_segments.append(primary_out_segment)

        primary_aligned = sorted(owners_aligned + contributors_aligned)
        if primary_aligned:
            role_segments.append(
                f"Owner/Contributor aligned: {', '.join(primary_aligned)}"
            )

        secondary_out_segment = _format_role_segment(
            "Informed/Affected out-of-sync",
            sorted(informed_out + affected_out),
            stakeholder_versions,
        )
        if secondary_out_segment:
            role_segments.append(secondary_out_segment)

        if observers_out:
            role_segments.append(
                f"Observer references lagging (lower priority): {', '.join(observers_out)}"
            )

        if role_segments:
            explanation = (
                f"Decision drift detected{when_clause}. "
                f"{' ; '.join(role_segments)}."
            )
        else:
            explanation = (
                f"Decision drift detected{when_clause}. "
                f"Out-of-sync stakeholders: {'; '.join(out_of_sync_details)}."
            )

    return {
        "decision_id": decision_id,
        "drift_detected": drift_detected,
        "latest_version": latest_version_label,
        "out_of_sync_stakeholders": sorted(out_of_sync_stakeholders),
        "explanation": explanation,
    }
