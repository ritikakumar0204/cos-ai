from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import networkx as nx

from ..core.decision_graph import add_decision, add_decision_version
from ..core.stakeholders import (
    add_stakeholder,
    compute_routing_targets,
    link_stakeholder_to_decision,
    link_stakeholder_to_version,
)
from ..core.version_resolution import get_latest_decision_version
from ..models.org_memory import get_project_graph, record_event, save_project_graph

try:
    from .briefing_agent import HuggingFaceLocalLLM
except Exception:  # pragma: no cover
    HuggingFaceLocalLLM = None  # type: ignore[assignment]


@dataclass
class StakeholderInput:
    """Input contract for stakeholder updates."""

    stakeholder_id: str
    name: str
    department: str
    role: str


class MeetingExtractionLLM(Protocol):
    """Interface for converting unstructured meeting text into decisions."""

    def generate(self, prompt: str, max_new_tokens: int = 220) -> str:
        """Generate text output for a prompt."""


class MemoryAgent:
    """State-management agent that updates project graphs deterministically."""

    def __init__(self, extraction_llm: MeetingExtractionLLM | None = None) -> None:
        self._extraction_llm = extraction_llm
        if self._extraction_llm is None and HuggingFaceLocalLLM is not None:
            try:
                self._extraction_llm = HuggingFaceLocalLLM()
            except Exception:
                self._extraction_llm = None

    @staticmethod
    def _decision_node_id(decision_id: str) -> str:
        return f"decision:{decision_id}"

    @staticmethod
    def _version_node_id(version_id: str) -> str:
        return f"decision_version:{version_id}"

    @staticmethod
    def _stakeholder_node_id(stakeholder_id: str) -> str:
        return f"stakeholder:{stakeholder_id}"

    def _upsert_decision(self, graph: nx.DiGraph, project_id: str, decision_id: str, title: str) -> None:
        decision_node = self._decision_node_id(decision_id)
        if decision_node not in graph:
            add_decision(graph, decision_id=decision_id, title=title)
        graph.nodes[decision_node]["project_id"] = project_id

    def _upsert_decision_version(
        self,
        graph: nx.DiGraph,
        project_id: str,
        decision_id: str,
        version_id: str,
        content: str,
        confidence: float,
        reasoning: str,
    ) -> None:
        version_node = self._version_node_id(version_id)
        if version_node not in graph:
            try:
                previous_latest = get_latest_decision_version(graph, decision_id)
            except ValueError:
                previous_latest = None

            add_decision_version(
                graph,
                version_id=version_id,
                decision_id=decision_id,
                content=content,
                confidence=confidence,
                reasoning=reasoning,
            )

            if previous_latest is not None and previous_latest != version_node:
                graph.add_edge(version_node, previous_latest, type="supersedes")

        graph.nodes[version_node]["project_id"] = project_id

    def _upsert_stakeholder(self, graph: nx.DiGraph, project_id: str, person: StakeholderInput) -> None:
        add_stakeholder(
            graph,
            stakeholder_id=person.stakeholder_id,
            name=person.name,
            department=person.department,
            role=person.role,
            scoped_projects=[project_id],
        )

    def _link_person(
        self,
        graph: nx.DiGraph,
        stakeholder_id: str,
        decision_id: str,
        version_id: str,
    ) -> None:
        try:
            link_stakeholder_to_decision(
                graph, stakeholder_id=stakeholder_id, decision_id=decision_id
            )
        except ValueError:
            pass

        try:
            link_stakeholder_to_version(
                graph, stakeholder_id=stakeholder_id, version_id=version_id
            )
        except ValueError:
            pass

    @staticmethod
    def _default_version_id(meeting_id: str) -> str:
        return f"{meeting_id}-v1"

    @staticmethod
    def _slug_from_title(title: str, default: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        return slug[:36] if slug else default

    def _extract_decisions_from_summary(
        self,
        project_id: str,
        meeting_id: str,
        title: str,
        summary: str,
    ) -> list[dict[str, Any]]:
        if not summary.strip():
            return []

        if self._extraction_llm is not None:
            prompt = (
                "Extract 1-3 concrete decisions from this meeting text.\n"
                "Return strict JSON object with key 'decisions' as array.\n"
                "Each decision item must include: decision_id, title, version_id, content, confidence, reasoning.\n"
                f"project_id={project_id}\n"
                f"meeting_id={meeting_id}\n"
                f"meeting_title={title}\n"
                f"meeting_summary={summary}\n"
            )
            try:
                raw = self._extraction_llm.generate(prompt, max_new_tokens=260)
                parsed = json.loads(raw)
                decisions = parsed.get("decisions", [])
                if isinstance(decisions, list):
                    cleaned: list[dict[str, Any]] = []
                    for item in decisions:
                        if not isinstance(item, dict):
                            continue
                        decision_title = str(item.get("title", title)).strip() or title
                        decision_id = str(
                            item.get("decision_id")
                            or f"dec-{self._slug_from_title(decision_title, 'auto')}"
                        )
                        cleaned.append(
                            {
                                "decision_id": decision_id,
                                "title": decision_title,
                                "version_id": str(item.get("version_id") or self._default_version_id(meeting_id)),
                                "content": str(item.get("content", summary)).strip() or summary,
                                "confidence": float(item.get("confidence", 0.7)),
                                "reasoning": str(item.get("reasoning", "Extracted from meeting summary")),
                            }
                        )
                    if cleaned:
                        return cleaned
            except Exception:
                pass

        # Deterministic fallback when no extractor is available or parsing fails.
        decision_title = title.strip() or "Meeting decision"
        decision_id = f"dec-{self._slug_from_title(decision_title, 'auto')}"
        return [
            {
                "decision_id": decision_id,
                "title": decision_title,
                "version_id": self._default_version_id(meeting_id),
                "content": summary.strip(),
                "confidence": 0.6,
                "reasoning": "Fallback extraction from meeting summary.",
            }
        ]

    def process_meeting(
        self,
        project_id: str,
        meeting_id: str,
        title: str,
        summary: str,
        decisions: list[dict[str, Any]],
        participants: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Ingest meeting outcomes into the graph and return routing previews."""
        graph = get_project_graph(project_id)
        decisions_to_process = decisions or self._extract_decisions_from_summary(
            project_id=project_id,
            meeting_id=meeting_id,
            title=title,
            summary=summary,
        )

        updated_decisions: list[dict[str, str]] = []
        routing: dict[str, dict[str, list[str]]] = {}

        participants_input = [StakeholderInput(**person) for person in participants]

        for decision in decisions_to_process:
            decision_id = decision["decision_id"]
            decision_title = decision.get("title", decision_id)
            version_id = decision["version_id"]
            content = decision.get("content", "")
            confidence = float(decision.get("confidence", 0.75))
            reasoning = decision.get("reasoning", "Captured from meeting summary")

            self._upsert_decision(graph, project_id, decision_id, decision_title)
            self._upsert_decision_version(
                graph,
                project_id,
                decision_id,
                version_id,
                content,
                confidence,
                reasoning,
            )

            for person in participants_input:
                self._upsert_stakeholder(graph, project_id, person)
                self._link_person(graph, person.stakeholder_id, decision_id, version_id)

            routing[decision_id] = compute_routing_targets(graph, decision_id, version_id)
            updated_decisions.append(
                {
                    "decision_id": decision_id,
                    "version_id": version_id,
                }
            )

        event = record_event(
            project_id,
            "meeting_processed",
            {
                "meeting_id": meeting_id,
                "title": title,
                "summary": summary,
                "updated_decisions": updated_decisions,
                "source": "structured_input" if decisions else "llm_extraction",
            },
        )
        save_project_graph(project_id)

        return {
            "event": event,
            "updated_decisions": updated_decisions,
            "routing": routing,
        }

    def stamp_decision_and_route(
        self,
        project_id: str,
        decision_id: str,
        title: str,
        version_id: str,
        content: str,
        confidence: float,
        reasoning: str,
        stakeholders: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Version-stamp a decision update and compute routing targets."""
        graph = get_project_graph(project_id)

        self._upsert_decision(graph, project_id, decision_id, title)
        self._upsert_decision_version(
            graph,
            project_id,
            decision_id,
            version_id,
            content,
            confidence,
            reasoning,
        )

        for person_data in stakeholders:
            person = StakeholderInput(**person_data)
            self._upsert_stakeholder(graph, project_id, person)
            self._link_person(graph, person.stakeholder_id, decision_id, version_id)

        routing = compute_routing_targets(graph, decision_id, version_id)

        event = record_event(
            project_id,
            "decision_version_stamped",
            {
                "decision_id": decision_id,
                "version_id": version_id,
                "title": title,
                "reasoning": reasoning,
            },
        )
        save_project_graph(project_id)

        return {
            "event": event,
            "decision_id": decision_id,
            "latest_version": version_id,
            "routing": routing,
        }

    def add_stakeholder_and_context(
        self,
        project_id: str,
        stakeholder: dict[str, str],
    ) -> dict[str, Any]:
        """Add a stakeholder to project scope and return insertion metadata."""
        graph = get_project_graph(project_id)
        person = StakeholderInput(**stakeholder)
        self._upsert_stakeholder(graph, project_id, person)

        event = record_event(
            project_id,
            "stakeholder_added",
            {
                "stakeholder_id": person.stakeholder_id,
                "name": person.name,
                "department": person.department,
                "role": person.role,
            },
        )
        save_project_graph(project_id)

        return {
            "event": event,
            "stakeholder_id": person.stakeholder_id,
        }
