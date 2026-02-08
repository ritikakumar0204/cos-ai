from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import networkx as nx


_GRAPHS: dict[str, nx.DiGraph] = {}
_EVENTS: dict[str, list[dict[str, Any]]] = {}
_LOCK = Lock()
_LOADED = False


def _storage_path() -> Path:
    raw = os.getenv("MCP_ORG_MEMORY_STORE_PATH", "backend/data/org_memory.json")
    return Path(raw)


def _serialize_graph(graph: nx.DiGraph) -> dict[str, Any]:
    data = nx.node_link_data(graph)
    links = data.get("links")
    edges = data.get("edges")
    return {
        "nodes": data.get("nodes", []),
        "links": links if isinstance(links, list) else (edges if isinstance(edges, list) else []),
        "edges": edges if isinstance(edges, list) else (links if isinstance(links, list) else []),
    }


def _deserialize_graph(payload: dict[str, Any]) -> nx.DiGraph:
    edge_key = "edges" if "edges" in payload else "links"
    return nx.node_link_graph(
        {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": payload.get("nodes", []),
            edge_key: payload.get(edge_key, []),
        },
        edges=edge_key,
    )


def _load_from_disk_locked() -> None:
    global _LOADED
    if _LOADED:
        return

    path = _storage_path()
    if not path.exists():
        _LOADED = True
        return

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _LOADED = True
        return

    for project_id, graph_payload in payload.get("graphs", {}).items():
        if isinstance(project_id, str) and isinstance(graph_payload, dict):
            _GRAPHS[project_id] = _deserialize_graph(graph_payload)

    for project_id, events in payload.get("events", {}).items():
        if isinstance(project_id, str) and isinstance(events, list):
            sanitized = [event for event in events if isinstance(event, dict)]
            _EVENTS[project_id] = sanitized

    _LOADED = True


def _persist_to_disk_locked() -> None:
    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "graphs": {project_id: _serialize_graph(graph) for project_id, graph in _GRAPHS.items()},
        "events": _EVENTS,
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def get_project_graph(project_id: str) -> nx.DiGraph:
    """Return the in-memory graph for a project, creating it if missing."""
    with _LOCK:
        _load_from_disk_locked()
        graph = _GRAPHS.get(project_id)
        if graph is None:
            graph = nx.DiGraph()
            _GRAPHS[project_id] = graph
            _persist_to_disk_locked()
        return graph


def record_event(project_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append an immutable event record for timeline and audit views."""
    event = {
        "event_type": event_type,
        "timestamp": _now(),
        "payload": dict(payload),
    }
    with _LOCK:
        _load_from_disk_locked()
        _EVENTS.setdefault(project_id, []).append(event)
        _persist_to_disk_locked()
    return event


def list_events(project_id: str) -> list[dict[str, Any]]:
    """Return all known events for a project in insertion order."""
    with _LOCK:
        _load_from_disk_locked()
        return [dict(event) for event in _EVENTS.get(project_id, [])]


def save_project_graph(project_id: str) -> None:
    """Persist graph + events after in-memory graph mutations."""
    with _LOCK:
        _load_from_disk_locked()
        if project_id in _GRAPHS:
            _persist_to_disk_locked()


def clear_org_memory() -> None:
    """Reset all in-memory project graphs/events (intended for tests)."""
    global _LOADED
    with _LOCK:
        _GRAPHS.clear()
        _EVENTS.clear()
        _LOADED = True
        path = _storage_path()
        if path.exists():
            path.unlink()
