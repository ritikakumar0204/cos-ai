from __future__ import annotations

from collections import defaultdict
import copy
import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

import networkx as nx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.memory_agent import MemoryAgent
from ..core.decision_graph import record_reference
from ..core.stakeholders import add_stakeholder, compute_routing_targets
from ..core.version_resolution import get_latest_decision_version
from ..models.org_memory import clear_org_memory, get_project_graph, list_events, record_event

router = APIRouter(tags=["projects"])


PROJECTS = [
    {"project_id": "proj-1", "project_name": "Analytics Platform"},
    {"project_id": "proj-2", "project_name": "Customer Portal"},
    {"project_id": "proj-3", "project_name": "Internal Tools"},
]


PROJECT_STAKEHOLDERS: dict[str, list[dict[str, str]]] = {
    "proj-1": [
        {"stakeholder_id": "s-1", "name": "Maya Chen", "department": "product", "role": "Owner"},
        {"stakeholder_id": "s-2", "name": "Jordan Lee", "department": "engineering", "role": "Contributor"},
        {"stakeholder_id": "s-3", "name": "Alex Rivera", "department": "infrastructure", "role": "Affected"},
        {"stakeholder_id": "s-4", "name": "Taylor Kim", "department": "finance", "role": "Informed"},
        {"stakeholder_id": "s-5", "name": "Casey Morgan", "department": "operations", "role": "Observer"},
        {"stakeholder_id": "s-13", "name": "Ava Brooks", "department": "product", "role": "Contributor"},
        {"stakeholder_id": "s-14", "name": "Noah Simmons", "department": "product", "role": "Contributor"},
        {"stakeholder_id": "s-15", "name": "Liam Foster", "department": "product", "role": "Informed"},
        {"stakeholder_id": "s-16", "name": "Emma Collins", "department": "operations", "role": "Affected"},
    ],
    "proj-2": [
        {"stakeholder_id": "s-6", "name": "Riley Park", "department": "product", "role": "Owner"},
        {"stakeholder_id": "s-7", "name": "Sam Patel", "department": "engineering", "role": "Contributor"},
        {"stakeholder_id": "s-8", "name": "Morgan West", "department": "operations", "role": "Affected"},
        {"stakeholder_id": "s-9", "name": "Jamie Quinn", "department": "infrastructure", "role": "Informed"},
    ],
    "proj-3": [
        {"stakeholder_id": "s-10", "name": "Priya Nair", "department": "engineering", "role": "Owner"},
        {"stakeholder_id": "s-11", "name": "Nina Das", "department": "infrastructure", "role": "Contributor"},
        {"stakeholder_id": "s-12", "name": "Arjun Rao", "department": "operations", "role": "Affected"},
    ],
}


MANAGER_REPORTS: dict[str, dict[str, list[str]]] = {
    "proj-1": {
        "s-1": ["s-4", "s-5", "s-13", "s-14", "s-15", "s-16"],
    }
}


MEETING_CATALOG: dict[str, list[dict[str, Any]]] = {
    "proj-1": [
        {
            "meeting_id": "m-1",
            "title": "Analytics Planning",
            "timestamp": "2026-02-10T10:00:00Z",
            "summary": "Initial analytics datastore discussion.",
            "participants": [
                {"stakeholder_id": "s-1", "name": "Maya Chen", "department": "product", "role": "Owner"},
                {"stakeholder_id": "s-2", "name": "Jordan Lee", "department": "engineering", "role": "Contributor"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-1",
                    "title": "Analytics Database Selection",
                    "version_id": "dec-1-v1",
                    "content": "Use Postgres for analytics MVP",
                    "confidence": 0.88,
                    "reasoning": "Fastest path for MVP delivery.",
                }
            ],
        },
        {
            "meeting_id": "m-2",
            "title": "Infra Review",
            "timestamp": "2026-02-11T15:30:00Z",
            "summary": "Re-evaluated datastore for scale.",
            "participants": [
                {"stakeholder_id": "s-2", "name": "Jordan Lee", "department": "engineering", "role": "Contributor"},
                {"stakeholder_id": "s-3", "name": "Alex Rivera", "department": "infrastructure", "role": "Owner"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-1",
                    "title": "Analytics Database Selection",
                    "version_id": "dec-1-v2",
                    "content": "Switch to BigQuery for scale needs",
                    "confidence": 0.91,
                    "reasoning": "Load projections exceed Postgres comfort range.",
                }
            ],
        },
        {
            "meeting_id": "m-3",
            "title": "Q1 Roadmap Sync",
            "timestamp": "2026-02-12T11:00:00Z",
            "summary": "Platform prioritization update.",
            "participants": [
                {"stakeholder_id": "s-1", "name": "Maya Chen", "department": "product", "role": "Owner"},
                {"stakeholder_id": "s-2", "name": "Jordan Lee", "department": "engineering", "role": "Contributor"},
                {"stakeholder_id": "s-5", "name": "Casey Morgan", "department": "operations", "role": "Affected"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-2",
                    "title": "Mobile vs Desktop Priority",
                    "version_id": "dec-2-v1",
                    "content": "Prioritize mobile experience over desktop",
                    "confidence": 0.86,
                    "reasoning": "Most usage now comes from mobile sessions.",
                },
                {
                    "decision_id": "dec-6",
                    "title": "API v2 Launch Timing",
                    "version_id": "dec-6-v1",
                    "content": "Delay API v2 launch to Q2",
                    "confidence": 0.83,
                    "reasoning": "Roadmap capacity constraints require focus on mobile delivery first.",
                },
            ],
        },
        {
            "meeting_id": "m-4",
            "title": "Security Review",
            "timestamp": "2026-02-14T13:15:00Z",
            "summary": "Security requirements for launch readiness.",
            "participants": [
                {"stakeholder_id": "s-2", "name": "Jordan Lee", "department": "engineering", "role": "Contributor"},
                {"stakeholder_id": "s-3", "name": "Alex Rivera", "department": "infrastructure", "role": "Owner"},
                {"stakeholder_id": "s-16", "name": "Emma Collins", "department": "operations", "role": "Affected"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-7",
                    "title": "SSO Requirement",
                    "version_id": "dec-7-v1",
                    "content": "Implement SSO before public launch",
                    "confidence": 0.9,
                    "reasoning": "Enterprise customers require SSO and auditability at launch.",
                }
            ],
        },
    ],
    "proj-2": [
        {
            "meeting_id": "m-5",
            "title": "Portal Kickoff",
            "timestamp": "2026-02-08T10:00:00Z",
            "summary": "Kickoff architecture agreements.",
            "participants": [
                {"stakeholder_id": "s-6", "name": "Riley Park", "department": "product", "role": "Owner"},
                {"stakeholder_id": "s-7", "name": "Sam Patel", "department": "engineering", "role": "Contributor"},
                {"stakeholder_id": "s-9", "name": "Jamie Quinn", "department": "infrastructure", "role": "Affected"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-3",
                    "title": "Authentication Approach",
                    "version_id": "dec-3-v1",
                    "content": "Use existing auth service",
                    "confidence": 0.93,
                    "reasoning": "Avoids rebuilding auth and keeps launch date intact.",
                }
            ],
        },
        {
            "meeting_id": "m-6",
            "title": "UX Review",
            "timestamp": "2026-02-13T16:00:00Z",
            "summary": "Standardized UI direction for customer-facing screens.",
            "participants": [
                {"stakeholder_id": "s-6", "name": "Riley Park", "department": "product", "role": "Owner"},
                {"stakeholder_id": "s-7", "name": "Sam Patel", "department": "engineering", "role": "Contributor"},
                {"stakeholder_id": "s-8", "name": "Morgan West", "department": "operations", "role": "Affected"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-4",
                    "title": "Design System Adoption",
                    "version_id": "dec-4-v1",
                    "content": "Adopt new design system for all customer-facing pages",
                    "confidence": 0.88,
                    "reasoning": "Creates consistency, improves accessibility, and reduces long-term UI drift.",
                }
            ],
        },
    ],
    "proj-3": [
        {
            "meeting_id": "m-7",
            "title": "Tooling Standup",
            "timestamp": "2026-02-09T11:00:00Z",
            "summary": "Consolidation decision for tooling repos.",
            "participants": [
                {"stakeholder_id": "s-10", "name": "Priya Nair", "department": "engineering", "role": "Owner"},
                {"stakeholder_id": "s-11", "name": "Nina Das", "department": "infrastructure", "role": "Contributor"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-5",
                    "title": "Monorepo Migration",
                    "version_id": "dec-5-v1",
                    "content": "Migrate scripts to monorepo",
                    "confidence": 0.85,
                    "reasoning": "Reduces duplication and simplifies CI maintenance.",
                }
            ],
        },
        {
            "meeting_id": "m-8",
            "title": "DevOps Sync",
            "timestamp": "2026-02-15T14:30:00Z",
            "summary": "Agreed to standardize delivery workflows across teams.",
            "participants": [
                {"stakeholder_id": "s-10", "name": "Priya Nair", "department": "engineering", "role": "Owner"},
                {"stakeholder_id": "s-11", "name": "Nina Das", "department": "infrastructure", "role": "Contributor"},
                {"stakeholder_id": "s-12", "name": "Arjun Rao", "department": "operations", "role": "Affected"},
            ],
            "decisions": [
                {
                    "decision_id": "dec-8",
                    "title": "CI Pipeline Standardization",
                    "version_id": "dec-8-v1",
                    "content": "Standardize CI pipelines across teams",
                    "confidence": 0.89,
                    "reasoning": "Improves delivery reliability and reduces maintenance overhead.",
                }
            ],
        },
    ],
}

_DEFAULT_PROJECTS = copy.deepcopy(PROJECTS)
_DEFAULT_PROJECT_STAKEHOLDERS = copy.deepcopy(PROJECT_STAKEHOLDERS)
_DEFAULT_MANAGER_REPORTS = copy.deepcopy(MANAGER_REPORTS)
_DEFAULT_MEETING_CATALOG = copy.deepcopy(MEETING_CATALOG)


def _dataset_path() -> Path:
    raw = os.getenv("MCP_DEMO_DATASET_PATH", "backend/data/demo_dataset.json")
    return Path(raw)


def _load_demo_dataset() -> dict[str, Any] | None:
    path = _dataset_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    return data


def _apply_demo_dataset() -> None:
    global PROJECTS, PROJECT_STAKEHOLDERS, MANAGER_REPORTS, MEETING_CATALOG

    data = _load_demo_dataset()
    if data is None:
        PROJECTS = copy.deepcopy(_DEFAULT_PROJECTS)
        PROJECT_STAKEHOLDERS = copy.deepcopy(_DEFAULT_PROJECT_STAKEHOLDERS)
        MANAGER_REPORTS = copy.deepcopy(_DEFAULT_MANAGER_REPORTS)
        MEETING_CATALOG = copy.deepcopy(_DEFAULT_MEETING_CATALOG)
        return

    projects = data.get("projects")
    stakeholders = data.get("project_stakeholders")
    reports = data.get("manager_reports")
    meetings = data.get("meeting_catalog")

    if isinstance(projects, list):
        PROJECTS = projects
    if isinstance(stakeholders, dict):
        PROJECT_STAKEHOLDERS = stakeholders
    if isinstance(reports, dict):
        MANAGER_REPORTS = reports
    if isinstance(meetings, dict):
        MEETING_CATALOG = meetings


_apply_demo_dataset()


MEETING_STATES: dict[str, dict[str, str]] = defaultdict(dict)
_STATE_LOCK = Lock()


class MeetingReviewRequest(BaseModel):
    action: str


class AcceptLatestDecisionRequest(BaseModel):
    include_downstream: bool = True


class CosVoiceMessageRequest(BaseModel):
    target_stakeholder_id: str
    target_stakeholder_name: str
    transcript: str


_ROLE_TO_ALIGNMENT_ROLE: dict[str, str] = {
    "Owner": "owner",
    "Contributor": "contributor",
    "Informed": "informed",
    "Affected": "affected",
    "Observer": "observer",
}

_ROLE_TO_AUTHORITY: dict[str, str] = {
    "Owner": "lead",
    "Contributor": "manager",
    "Informed": "senior_ic",
    "Affected": "senior_ic",
    "Observer": "ic",
}

_STATUS_PRIORITY: dict[str, int] = {
    "out_of_sync": 3,
    "awaiting_update": 2,
    "aligned": 1,
}


def _project_exists(project_id: str) -> bool:
    return any(p["project_id"] == project_id for p in PROJECTS)


def _find_meeting(project_id: str, meeting_id: str) -> dict[str, Any] | None:
    for meeting in MEETING_CATALOG.get(project_id, []):
        if meeting["meeting_id"] == meeting_id:
            return meeting
    return None


def _get_meeting_state(project_id: str, meeting_id: str) -> str:
    with _STATE_LOCK:
        return MEETING_STATES[project_id].get(meeting_id, "pending")


def _set_meeting_state(project_id: str, meeting_id: str, state: str) -> None:
    with _STATE_LOCK:
        MEETING_STATES[project_id][meeting_id] = state


def _ensure_project_stakeholders_in_graph(project_id: str) -> None:
    graph = get_project_graph(project_id)
    for stakeholder in PROJECT_STAKEHOLDERS.get(project_id, []):
        add_stakeholder(
            graph,
            stakeholder_id=stakeholder["stakeholder_id"],
            name=stakeholder["name"],
            department=stakeholder["department"],
            role=stakeholder["role"],
            scoped_projects=[project_id],
        )


def _stakeholder_lookup(project_id: str) -> dict[str, dict[str, str]]:
    return {
        stakeholder["stakeholder_id"]: stakeholder
        for stakeholder in PROJECT_STAKEHOLDERS.get(project_id, [])
    }


def _find_stakeholder(project_id: str, stakeholder_id: str) -> dict[str, str] | None:
    return _stakeholder_lookup(project_id).get(stakeholder_id)


def _collect_downstream_stakeholders(project_id: str, manager_id: str) -> list[dict[str, str]]:
    lookup = _stakeholder_lookup(project_id)
    reports_map = MANAGER_REPORTS.get(project_id, {})

    collected_ids: list[str] = []
    queue = list(reports_map.get(manager_id, []))
    seen: set[str] = set()

    while queue:
        stakeholder_id = queue.pop(0)
        if stakeholder_id in seen:
            continue
        seen.add(stakeholder_id)
        if stakeholder_id in lookup:
            collected_ids.append(stakeholder_id)
        queue.extend(reports_map.get(stakeholder_id, []))

    return [lookup[stakeholder_id] for stakeholder_id in collected_ids]


def _latest_version_ids_for_project(graph: nx.DiGraph, project_id: str) -> dict[str, str]:
    latest: dict[str, str] = {}
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") != "decision" or attrs.get("project_id") != project_id:
            continue
        decision_id = str(attrs.get("decision_id", ""))
        if not decision_id:
            continue
        try:
            latest_node = get_latest_decision_version(graph, decision_id)
        except ValueError:
            continue
        version_id = str(graph.nodes[latest_node].get("version_id", ""))
        if version_id:
            latest[decision_id] = version_id
    return latest


def _ack_latest_versions_for_stakeholders(
    project_id: str,
    stakeholder_ids: list[str],
) -> dict[str, Any]:
    _ensure_project_stakeholders_in_graph(project_id)
    graph = get_project_graph(project_id)
    latest_versions = _latest_version_ids_for_project(graph, project_id)
    acknowledged: dict[str, list[str]] = defaultdict(list)

    for decision_id, version_id in latest_versions.items():
        for stakeholder_id in stakeholder_ids:
            try:
                record_reference(graph, version_id=version_id, stakeholder_id=stakeholder_id)
            except ValueError:
                continue
            acknowledged[decision_id].append(stakeholder_id)

    return {
        "latest_versions": latest_versions,
        "acknowledged": acknowledged,
    }


def _safe_latest_version(graph: nx.DiGraph, decision_id: str) -> str | None:
    try:
        latest_node = get_latest_decision_version(graph, decision_id)
        return str(graph.nodes[latest_node].get("version_id") or "")
    except ValueError:
        return None


def _mark_attendance_drift(
    project_id: str,
    attendees: set[str],
    previous_versions: dict[str, str | None],
) -> None:
    graph = get_project_graph(project_id)
    for decision_id, previous_version in previous_versions.items():
        if not previous_version:
            continue

        # Build decision-local version nodes once so we can reset references deterministically.
        decision_node = f"decision:{decision_id}"
        version_nodes: list[str] = []
        if decision_node in graph:
            for _, version_node, edge_data in graph.out_edges(decision_node, data=True):
                if edge_data.get("type") == "has_version" and graph.nodes[version_node].get("type") == "decision_version":
                    version_nodes.append(version_node)

        for stakeholder in PROJECT_STAKEHOLDERS.get(project_id, []):
            stakeholder_id = stakeholder["stakeholder_id"]
            if stakeholder_id in attendees:
                continue
            stakeholder_node = f"stakeholder:{stakeholder_id}"
            if stakeholder_node in graph:
                # Ensure one effective reference per decision for non-attendees.
                for version_node in version_nodes:
                    if graph.has_edge(version_node, stakeholder_node) and graph.edges[version_node, stakeholder_node].get(
                        "type"
                    ) == "referenced_by":
                        graph.remove_edge(version_node, stakeholder_node)
            try:
                record_reference(graph, version_id=previous_version, stakeholder_id=stakeholder_id)
            except ValueError:
                # Skip invalid graph links for unrelated decisions/stakeholders.
                continue


def _record_attendee_acknowledgement(attendees: list[dict[str, str]], version_id: str, project_id: str) -> None:
    graph = get_project_graph(project_id)
    for participant in attendees:
        try:
            record_reference(
                graph,
                version_id=version_id,
                stakeholder_id=participant["stakeholder_id"],
            )
        except ValueError:
            continue


def _approve_meeting(project_id: str, meeting: dict[str, Any]) -> None:
    graph = get_project_graph(project_id)
    memory = MemoryAgent()

    previous_versions: dict[str, str | None] = {}
    for decision in meeting["decisions"]:
        decision_id = decision["decision_id"]
        previous_versions[decision_id] = _safe_latest_version(graph, decision_id)

    memory.process_meeting(
        project_id=project_id,
        meeting_id=meeting["meeting_id"],
        title=meeting["title"],
        summary=meeting.get("summary", ""),
        decisions=meeting["decisions"],
        participants=meeting["participants"],
    )

    attendee_ids = {p["stakeholder_id"] for p in meeting["participants"]}
    _mark_attendance_drift(project_id=project_id, attendees=attendee_ids, previous_versions=previous_versions)

    for decision in meeting["decisions"]:
        _record_attendee_acknowledgement(meeting["participants"], decision["version_id"], project_id)


def _meeting_response(project_id: str, meeting: dict[str, Any]) -> dict[str, Any]:
    state = _get_meeting_state(project_id, meeting["meeting_id"])
    return {
        "meeting_id": meeting["meeting_id"],
        "title": meeting["title"],
        "timestamp": meeting["timestamp"],
        "date": meeting["timestamp"],
        "summary": meeting.get("summary", ""),
        "status": state,
        "locked": state == "approved",
        "departments_present": [p["department"] for p in meeting["participants"]],
        "decisions_extracted": [d["content"] for d in meeting["decisions"]],
    }


def _map_role(role: str) -> str:
    return _ROLE_TO_ALIGNMENT_ROLE.get(role, "observer")


def _collect_references_for_decision(graph: nx.DiGraph, version_nodes: list[str]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)
    for version_node in version_nodes:
        version_id = str(graph.nodes[version_node].get("version_id", ""))
        for _, stakeholder_node, edge_data in graph.out_edges(version_node, data=True):
            if edge_data.get("type") != "referenced_by":
                continue
            stakeholder_id = graph.nodes[stakeholder_node].get("stakeholder_id")
            if stakeholder_id:
                refs[str(stakeholder_id)].add(version_id)
    return refs


def _stakeholders_for_version(
    graph: nx.DiGraph,
    decision_node: str,
    version_node: str,
    refs: dict[str, set[str]],
    latest_version: str,
) -> list[dict[str, str]]:
    stakeholder_nodes: set[str] = set()

    for source, _, edge_data in graph.in_edges(decision_node, data=True):
        if edge_data.get("type") in {"owns", "contributes"} and graph.nodes[source].get("type") == "stakeholder":
            stakeholder_nodes.add(source)

    for source, _, edge_data in graph.in_edges(version_node, data=True):
        if edge_data.get("type") in {"informed_of", "affected_by"} and graph.nodes[source].get("type") == "stakeholder":
            stakeholder_nodes.add(source)

    for _, target, edge_data in graph.out_edges(version_node, data=True):
        if edge_data.get("type") == "referenced_by" and graph.nodes[target].get("type") == "stakeholder":
            stakeholder_nodes.add(target)

    version_id = str(graph.nodes[version_node].get("version_id", ""))
    stakeholders: list[dict[str, str]] = []

    for node in sorted(stakeholder_nodes):
        attrs = graph.nodes[node]
        stakeholder_id = str(attrs.get("stakeholder_id", ""))
        if not stakeholder_id:
            continue

        referenced = refs.get(stakeholder_id, set())
        if latest_version in referenced:
            status = "aligned"
        elif referenced:
            status = "out_of_sync"
        elif version_id == latest_version:
            status = "awaiting_update"
        else:
            status = "aligned"

        stakeholders.append(
            {
                "id": stakeholder_id,
                "name": str(attrs.get("name", stakeholder_id)),
                "department": str(attrs.get("department", "operations")),
                "role": _map_role(str(attrs.get("role", "Observer"))),
                "status": status,
            }
        )

    return stakeholders


def _versions_for_decision(graph: nx.DiGraph, decision_node: str) -> list[str]:
    versions: list[str] = []
    for _, target, edge_data in graph.out_edges(decision_node, data=True):
        if edge_data.get("type") != "has_version":
            continue
        if graph.nodes[target].get("type") != "decision_version":
            continue
        versions.append(target)
    versions.sort(key=lambda node: str(graph.nodes[node].get("created_at", "")))
    return versions


def _decision_payload(graph: nx.DiGraph, decision_node: str) -> dict[str, Any]:
    decision_attrs = graph.nodes[decision_node]
    decision_id = str(decision_attrs.get("decision_id", ""))
    title = str(decision_attrs.get("title", decision_id))
    version_nodes = _versions_for_decision(graph, decision_node)

    if not decision_id or not version_nodes:
        return {}

    latest_node = get_latest_decision_version(graph, decision_id)
    latest_version = str(graph.nodes[latest_node].get("version_id", ""))
    refs = _collect_references_for_decision(graph, version_nodes)

    versions: list[dict[str, Any]] = []
    out_of_sync_people: set[str] = set()
    previous_content = ""

    for index, version_node in enumerate(version_nodes):
        attrs = graph.nodes[version_node]
        version_id = str(attrs.get("version_id", version_node))
        content = str(attrs.get("content", ""))
        stakeholders = _stakeholders_for_version(graph, decision_node, version_node, refs, latest_version)

        for stakeholder in stakeholders:
            if stakeholder["status"] == "out_of_sync":
                out_of_sync_people.add(stakeholder["name"])

        if index == 0:
            what_changed = "Initial decision baseline captured from an approved meeting."
        else:
            what_changed = f"Updated from prior version guidance to {version_id}."

        why_changed = str(attrs.get("reasoning", "Updated from approved meeting outcomes."))

        if previous_content and previous_content == content:
            what_changed = "No semantic change in decision content; traceability metadata was updated."

        versions.append(
            {
                "version_id": version_id,
                "content": content,
                "created_at": str(attrs.get("created_at", "")),
                "what_changed": what_changed,
                "why_changed": why_changed,
                "stakeholders": stakeholders,
            }
        )
        previous_content = content

    drifting = len(out_of_sync_people) > 0
    status = "drifting" if drifting else "active"
    insight = (
        "Drift detected: non-attendees are still referencing earlier decision versions."
        if drifting
        else "All tracked stakeholders are aligned to the current decision version."
    )

    return {
        "decision_id": decision_id,
        "title": title,
        "description": f"Decision history for {title.lower()}.",
        "status": status,
        "versions": versions,
        "latest_version": latest_version,
        "insight": insight,
    }


def _highest_status(first: str, second: str) -> str:
    return first if _STATUS_PRIORITY[first] >= _STATUS_PRIORITY[second] else second


def _stakeholder_reference_versions(graph: nx.DiGraph) -> tuple[dict[str, set[str]], dict[str, str]]:
    references: dict[str, set[str]] = defaultdict(set)
    version_times: dict[str, str] = {}

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") == "decision_version":
            version_id = str(attrs.get("version_id", ""))
            if version_id:
                version_times[version_id] = str(attrs.get("created_at", ""))

    for source, target, edge_data in graph.edges(data=True):
        if edge_data.get("type") != "referenced_by":
            continue
        source_data = graph.nodes[source]
        target_data = graph.nodes[target]
        version_id = str(source_data.get("version_id", ""))
        stakeholder_id = str(target_data.get("stakeholder_id", ""))
        if version_id and stakeholder_id:
            references[stakeholder_id].add(version_id)

    return references, version_times


def _pick_last_referenced_version(version_ids: set[str], version_times: dict[str, str]) -> str:
    if not version_ids:
        return ""
    return max(version_ids, key=lambda version_id: version_times.get(version_id, ""))


def _department_status(stakeholders: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in stakeholders}
    if "out_of_sync" in statuses:
        return "drifting"
    if "awaiting_update" in statuses:
        return "awaiting_update"
    return "aligned"


def _department_context(department_name: str, status: str, stakeholders: list[dict[str, str]]) -> str | None:
    if status == "drifting":
        names = [item["name"] for item in stakeholders if item["status"] == "out_of_sync"]
        if names:
            joined = ", ".join(names)
            return f"{joined} in {department_name} is still operating on older decision versions."
    if status == "awaiting_update":
        names = [item["name"] for item in stakeholders if item["status"] == "awaiting_update"]
        if names:
            joined = ", ".join(names)
            return f"{joined} in {department_name} has not acknowledged the latest approved decisions."
    return None


def _project_name(project_id: str) -> str:
    for project in PROJECTS:
        if project["project_id"] == project_id:
            return project["project_name"]
    return project_id


def _build_alignment_payload(project_id: str) -> dict[str, Any]:
    decisions = get_project_decisions(project_id)["decisions"]
    graph = get_project_graph(project_id)

    by_stakeholder: dict[str, dict[str, str]] = {}
    references, version_times = _stakeholder_reference_versions(graph)

    for decision in decisions:
        latest_version = decision.get("latest_version", "")
        versions = decision.get("versions", [])
        latest_payload = next((item for item in versions if item.get("version_id") == latest_version), None)
        if not latest_payload:
            continue

        for stakeholder in latest_payload.get("stakeholders", []):
            stakeholder_id = str(stakeholder.get("id", ""))
            if not stakeholder_id:
                continue
            existing = by_stakeholder.get(stakeholder_id)
            status = str(stakeholder.get("status", "awaiting_update"))
            role = str(stakeholder.get("role", "observer"))
            if existing is None:
                by_stakeholder[stakeholder_id] = {
                    "id": stakeholder_id,
                    "name": str(stakeholder.get("name", stakeholder_id)),
                    "department": str(stakeholder.get("department", "operations")),
                    "role": role,
                    "status": status,
                }
            else:
                existing["status"] = _highest_status(existing["status"], status)

    for stakeholder in PROJECT_STAKEHOLDERS.get(project_id, []):
        stakeholder_id = stakeholder["stakeholder_id"]
        if stakeholder_id in by_stakeholder:
            continue
        by_stakeholder[stakeholder_id] = {
            "id": stakeholder_id,
            "name": stakeholder["name"],
            "department": stakeholder["department"],
            "role": _map_role(stakeholder["role"]),
            "status": "awaiting_update",
        }

    by_department: dict[str, list[dict[str, str]]] = defaultdict(list)
    for stakeholder in by_stakeholder.values():
        stakeholder_id = stakeholder["id"]
        referenced = references.get(stakeholder_id, set())
        role_key = stakeholder["role"]
        source_role = role_key.capitalize()
        authority = _ROLE_TO_AUTHORITY.get(source_role, "ic")
        last_reference = _pick_last_referenced_version(referenced, version_times)

        by_department[stakeholder["department"]].append(
            {
                "id": stakeholder["id"],
                "name": stakeholder["name"],
                "role": role_key,
                "authority": authority,
                "status": stakeholder["status"],
                "lastVersionReferenced": last_reference or "none",
            }
        )

    departments: list[dict[str, Any]] = []
    drifting_departments: list[str] = []
    awaiting_departments: list[str] = []

    for department_id in sorted(by_department):
        stakeholders = sorted(by_department[department_id], key=lambda item: item["name"])
        status = _department_status(stakeholders)
        context = _department_context(department_id.capitalize(), status, stakeholders)

        if status == "drifting":
            drifting_departments.append(department_id)
        if status == "awaiting_update":
            awaiting_departments.append(department_id)

        payload: dict[str, Any] = {
            "department_id": department_id,
            "status": status,
            "stakeholders": stakeholders,
        }
        if context:
            payload["context"] = context
        departments.append(payload)

    if drifting_departments:
        summary = (
            "Current approved decision versions are not consistently reflected in "
            + ", ".join(drifting_departments)
            + "; those teams are referencing prior approved versions."
        )
    elif awaiting_departments:
        summary = (
            "No direct drift detected. Awaiting acknowledgements from "
            + ", ".join(awaiting_departments)
            + " on the latest approved decisions."
        )
    else:
        summary = "All tracked departments are aligned with the latest approved decision versions."

    return {
        "project_id": project_id,
        "project_name": _project_name(project_id),
        "alignment_status": "drift_detected" if drifting_departments else "aligned",
        "out_of_sync_departments": drifting_departments,
        "explanation": summary,
        "departments": departments,
        "summary": summary,
    }


@router.get("/projects")
def list_projects() -> list[dict[str, str]]:
    return PROJECTS


def reset_demo_state() -> None:
    clear_org_memory()
    with _STATE_LOCK:
        MEETING_STATES.clear()


@router.get("/projects/{project_id}/meetings")
def get_project_meetings(project_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    _ensure_project_stakeholders_in_graph(project_id)
    meetings = [_meeting_response(project_id, meeting) for meeting in MEETING_CATALOG.get(project_id, [])]
    return {"project_id": project_id, "meetings": meetings}


@router.post("/projects/{project_id}/meetings/{meeting_id}/review")
def review_meeting(project_id: str, meeting_id: str, payload: MeetingReviewRequest) -> dict[str, Any]:
    if payload.action not in {"approve", "deny"}:
        raise HTTPException(status_code=422, detail="action must be 'approve' or 'deny'.")
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    meeting = _find_meeting(project_id, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail=f"Meeting '{meeting_id}' not found in project '{project_id}'.")

    _ensure_project_stakeholders_in_graph(project_id)
    current_state = _get_meeting_state(project_id, meeting_id)

    if current_state == "approved":
        return {
            "project_id": project_id,
            "meeting_id": meeting_id,
            "status": "approved",
            "locked": True,
            "message": "Meeting already approved; state is immutable.",
        }

    if payload.action == "deny":
        _set_meeting_state(project_id, meeting_id, "denied")
        return {
            "project_id": project_id,
            "meeting_id": meeting_id,
            "status": "denied",
            "locked": False,
            "message": "Meeting denied. No graph updates applied.",
        }

    _approve_meeting(project_id, meeting)
    _set_meeting_state(project_id, meeting_id, "approved")
    return {
        "project_id": project_id,
        "meeting_id": meeting_id,
        "status": "approved",
        "locked": True,
        "message": "Meeting approved and graph updated.",
    }


@router.get("/projects/{project_id}/decisions")
def get_project_decisions(project_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    _ensure_project_stakeholders_in_graph(project_id)
    graph = get_project_graph(project_id)

    decision_nodes = [
        node_id
        for node_id, attrs in graph.nodes(data=True)
        if attrs.get("type") == "decision" and attrs.get("project_id") == project_id
    ]

    decisions = []
    for node in sorted(decision_nodes):
        payload = _decision_payload(graph, node)
        if payload:
            decisions.append(payload)

    return {"project_id": project_id, "decisions": decisions}


@router.get("/projects/{project_id}/alignment")
def get_project_alignment(project_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    _ensure_project_stakeholders_in_graph(project_id)
    return _build_alignment_payload(project_id)


@router.get("/projects/{project_id}/stakeholders/{stakeholder_id}/reports")
def get_stakeholder_reports(project_id: str, stakeholder_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    manager = _find_stakeholder(project_id, stakeholder_id)
    if manager is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stakeholder '{stakeholder_id}' not found in project '{project_id}'.",
        )

    reports = _collect_downstream_stakeholders(project_id, stakeholder_id)
    return {
        "project_id": project_id,
        "manager": manager,
        "reports": reports,
    }


@router.post("/projects/{project_id}/cos-voice-messages")
def save_cos_voice_message(project_id: str, payload: CosVoiceMessageRequest) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    stakeholder = _find_stakeholder(project_id, payload.target_stakeholder_id)
    if stakeholder is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Stakeholder '{payload.target_stakeholder_id}' not found in project '{project_id}'."
            ),
        )

    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Transcript cannot be empty.")

    event = record_event(
        project_id,
        "cos_voice_message",
        {
            "target_stakeholder_id": payload.target_stakeholder_id,
            "target_stakeholder_name": payload.target_stakeholder_name.strip() or stakeholder["name"],
            "transcript": transcript,
            "source": "cos",
        },
    )

    return {
        "project_id": project_id,
        "target_stakeholder_id": payload.target_stakeholder_id,
        "target_stakeholder_name": payload.target_stakeholder_name.strip() or stakeholder["name"],
        "transcript": transcript,
        "timestamp": event["timestamp"],
    }


@router.get("/projects/{project_id}/stakeholders/{stakeholder_id}/cos-voice-message")
def get_latest_cos_voice_message(project_id: str, stakeholder_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    if _find_stakeholder(project_id, stakeholder_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stakeholder '{stakeholder_id}' not found in project '{project_id}'.",
        )

    events = list_events(project_id)
    for event in reversed(events):
        if event.get("event_type") != "cos_voice_message":
            continue
        payload = event.get("payload", {})
        if payload.get("target_stakeholder_id") != stakeholder_id:
            continue
        transcript = str(payload.get("transcript", "")).strip()
        if not transcript:
            continue
        return {
            "project_id": project_id,
            "stakeholder_id": stakeholder_id,
            "source": str(payload.get("source", "cos")),
            "message": transcript,
            "timestamp": event.get("timestamp"),
        }

    return {
        "project_id": project_id,
        "stakeholder_id": stakeholder_id,
        "source": "cos",
        "message": "",
        "timestamp": None,
    }


@router.post("/projects/{project_id}/stakeholders/{stakeholder_id}/accept-latest")
def accept_latest_decisions(
    project_id: str,
    stakeholder_id: str,
    payload: AcceptLatestDecisionRequest,
) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    manager = _find_stakeholder(project_id, stakeholder_id)
    if manager is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stakeholder '{stakeholder_id}' not found in project '{project_id}'.",
        )

    downstream = _collect_downstream_stakeholders(project_id, stakeholder_id) if payload.include_downstream else []
    stakeholder_ids = [stakeholder_id, *[item["stakeholder_id"] for item in downstream]]
    ack_result = _ack_latest_versions_for_stakeholders(project_id, stakeholder_ids)
    latest_versions = ack_result["latest_versions"]
    acknowledged = {
        decision_id: sorted(set(stakeholders))
        for decision_id, stakeholders in ack_result["acknowledged"].items()
    }

    notified_people = [manager, *downstream]
    alignment = _build_alignment_payload(project_id)

    return {
        "project_id": project_id,
        "accepted_by": manager,
        "include_downstream": payload.include_downstream,
        "notified_stakeholders": notified_people,
        "latest_versions": latest_versions,
        "acknowledged_by_decision": acknowledged,
        "alignment_status": alignment["alignment_status"],
        "out_of_sync_departments": alignment["out_of_sync_departments"],
        "message": (
            "Latest decisions accepted and propagated to downstream team members."
            if payload.include_downstream
            else "Latest decisions accepted."
        ),
    }


@router.get("/projects/{project_id}/decisions/{decision_id}/routing-preview")
def get_routing_preview(project_id: str, decision_id: str) -> dict[str, Any]:
    if not _project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    graph = get_project_graph(project_id)
    decision_node = f"decision:{decision_id}"
    if decision_node not in graph:
        raise HTTPException(
            status_code=404,
            detail=f"Decision '{decision_id}' not found in project '{project_id}'.",
        )

    try:
        latest_node = get_latest_decision_version(graph, decision_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    latest_version = str(graph.nodes[latest_node].get("version_id", ""))
    routing = compute_routing_targets(graph, decision_id=decision_id, version_id=latest_version)

    stakeholders: dict[str, dict[str, str]] = {}
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") != "stakeholder":
            continue
        sid = attrs.get("stakeholder_id")
        if not sid:
            continue
        stakeholders[str(sid)] = {
            "stakeholder_id": str(sid),
            "name": str(attrs.get("name", sid)),
            "role": str(attrs.get("role", "Observer")),
        }

    return {
        "project_id": project_id,
        "decision_id": decision_id,
        "latest_version": latest_version,
        "routing": {
            "amplify": [stakeholders[s] for s in routing["amplify"] if s in stakeholders],
            "inform": [stakeholders[s] for s in routing["inform"] if s in stakeholders],
            "restrict": [stakeholders[s] for s in routing["restrict"] if s in stakeholders],
        },
    }
