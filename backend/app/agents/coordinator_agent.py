from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Protocol

from ..core.version_resolution import get_latest_decision_version
from ..models.org_memory import get_project_graph, list_events

try:
    from .briefing_agent import HuggingFaceLocalLLM
except Exception:  # pragma: no cover
    HuggingFaceLocalLLM = None  # type: ignore[assignment]


class CoordinatorLLM(Protocol):
    """Interface for LLM-assisted coordinator reasoning."""

    def generate(self, prompt: str, max_new_tokens: int = 220) -> str:
        """Generate output text for a prompt."""


class CoordinatorAgent:
    """Coordinator agent for change digests, visual maps, and context views."""

    def __init__(self, llm: CoordinatorLLM | None = None) -> None:
        self._llm = llm
        if self._llm is None and HuggingFaceLocalLLM is not None:
            try:
                self._llm = HuggingFaceLocalLLM()
            except Exception:
                self._llm = None

    @staticmethod
    def _matches_project(attrs: dict[str, Any], project_id: str) -> bool:
        if attrs.get("project_id") == project_id:
            return True
        scoped = attrs.get("scoped_projects")
        return isinstance(scoped, list) and project_id in scoped

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any] | None:
        if not text.strip():
            return None

        candidate = text.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            parsed = json.loads(candidate[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    @staticmethod
    def _clean_sentence(text: str, fallback: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned if cleaned else fallback

    def _llm_daily_digest(
        self,
        project_id: str,
        target_day: str,
        updates: list[dict[str, Any]],
        visual_map: dict[str, Any],
    ) -> str:
        fallback = (
            f"Project {project_id} has {len(updates)} recorded updates on {target_day}, "
            f"with {visual_map.get('node_count', 0)} nodes and {visual_map.get('edge_count', 0)} edges in the current map."
        )
        if self._llm is None:
            return fallback

        prompt = (
            "You are a coordination assistant.\n"
            "Given project updates and graph counts, write a concise 1-2 sentence daily digest.\n"
            "Return strict JSON object: {\"summary\": \"...\"}.\n"
            f"project_id={project_id}\n"
            f"date={target_day}\n"
            f"updates={json.dumps(updates, ensure_ascii=True)}\n"
            f"visual_map={{\"node_count\": {visual_map.get('node_count', 0)}, \"edge_count\": {visual_map.get('edge_count', 0)}}}\n"
        )

        try:
            raw = self._llm.generate(prompt, max_new_tokens=160)
            parsed = self._extract_json_object(raw)
            if parsed and isinstance(parsed.get("summary"), str):
                return self._clean_sentence(parsed["summary"], fallback)
        except Exception:
            pass

        return fallback

    def _llm_context_narrative(self, context: dict[str, Any]) -> str:
        fallback = (
            f"{context.get('name', context.get('stakeholder_id', 'Stakeholder'))} is linked to "
            f"{len(context.get('linked_decisions', []))} decisions and "
            f"{len(context.get('linked_versions', []))} decision versions."
        )
        if self._llm is None:
            return fallback

        prompt = (
            "You are a coordination assistant.\n"
            "Summarize this stakeholder context in 1 sentence using plain language.\n"
            "Return strict JSON object: {\"narrative\": \"...\"}.\n"
            f"context={json.dumps(context, ensure_ascii=True)}\n"
        )

        try:
            raw = self._llm.generate(prompt, max_new_tokens=140)
            parsed = self._extract_json_object(raw)
            if parsed and isinstance(parsed.get("narrative"), str):
                return self._clean_sentence(parsed["narrative"], fallback)
        except Exception:
            pass

        return fallback

    def changed_today(self, project_id: str, day: str | None = None) -> dict[str, Any]:
        """Return timeline updates for a given day and a graph map payload."""
        target_day = day or date.today().isoformat()
        events = list_events(project_id)
        todays = [
            event for event in events if str(event.get("timestamp", "")).startswith(target_day)
        ]
        todays.sort(key=lambda event: str(event.get("timestamp", "")), reverse=True)

        map_payload = self.visual_map(project_id)
        summary = self._llm_daily_digest(
            project_id=project_id,
            target_day=target_day,
            updates=todays,
            visual_map=map_payload,
        )

        return {
            "project_id": project_id,
            "date": target_day,
            "updates": todays,
            "visual_map": map_payload,
            "coordinator_summary": summary,
        }

    def visual_map(self, project_id: str) -> dict[str, Any]:
        """Return graph payload suitable for front-end visualization."""
        graph = get_project_graph(project_id)

        nodes: list[dict[str, Any]] = []
        for node_id, attrs in graph.nodes(data=True):
            if not self._matches_project(attrs, project_id) and attrs.get("type") != "stakeholder":
                continue

            nodes.append(
                {
                    "id": node_id,
                    "type": attrs.get("type", "unknown"),
                    "label": (
                        attrs.get("title")
                        or attrs.get("name")
                        or attrs.get("version_id")
                        or attrs.get("decision_id")
                        or node_id
                    ),
                }
            )

        node_ids = {node["id"] for node in nodes}

        edges: list[dict[str, str]] = []
        for source, target, attrs in graph.edges(data=True):
            if source not in node_ids and target not in node_ids:
                continue
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "type": attrs.get("type", "related_to"),
                }
            )

        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def stakeholder_context(self, project_id: str, stakeholder_id: str) -> dict[str, Any]:
        """Build an instant context view for a stakeholder in project scope."""
        graph = get_project_graph(project_id)
        stakeholder_node = f"stakeholder:{stakeholder_id}"

        if stakeholder_node not in graph:
            return {
                "project_id": project_id,
                "stakeholder_id": stakeholder_id,
                "exists": False,
                "context": "Stakeholder not present in project graph.",
            }

        attrs = graph.nodes[stakeholder_node]

        linked_decisions: list[dict[str, str]] = []
        for _, decision_node, edge_data in graph.out_edges(stakeholder_node, data=True):
            if edge_data.get("type") not in {"owns", "contributes"}:
                continue
            decision = graph.nodes[decision_node]
            decision_id = decision.get("decision_id")
            if not decision_id:
                continue
            try:
                latest = get_latest_decision_version(graph, decision_id)
                latest_label = graph.nodes[latest].get("version_id", latest)
            except ValueError:
                latest_label = "unknown"
            linked_decisions.append(
                {
                    "decision_id": decision_id,
                    "title": decision.get("title", decision_id),
                    "latest_version": str(latest_label),
                }
            )

        linked_versions: list[dict[str, str]] = []
        for _, version_node, edge_data in graph.out_edges(stakeholder_node, data=True):
            if edge_data.get("type") not in {"informed_of", "affected_by"}:
                continue
            version = graph.nodes[version_node]
            linked_versions.append(
                {
                    "version_id": version.get("version_id", version_node),
                    "decision_id": version.get("decision_id", "unknown"),
                }
            )

        context = {
            "project_id": project_id,
            "stakeholder_id": stakeholder_id,
            "exists": True,
            "name": attrs.get("name", stakeholder_id),
            "department": attrs.get("department", "unknown"),
            "role": attrs.get("role", "unknown"),
            "linked_decisions": linked_decisions,
            "linked_versions": linked_versions,
        }
        context["narrative"] = self._llm_context_narrative(context)
        return context
