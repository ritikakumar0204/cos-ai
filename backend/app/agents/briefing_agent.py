import json
import re
from datetime import datetime, timezone
from typing import Any, Protocol

import networkx as nx

from ..core.drift_detection import detect_decision_drift
from ..core.explanation_generator import generate_drift_explanation
from ..core.version_resolution import get_latest_decision_version

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover
    AutoModelForCausalLM = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]


class TextLLM(Protocol):
    """Simple text-generation interface used by briefing agents."""

    def generate(self, prompt: str, max_new_tokens: int = 220) -> str:
        """Generate a completion for the provided prompt."""


class HuggingFaceLocalLLM:
    """Minimal HuggingFace-backed local LLM adapter."""

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2") -> None:
        self.model_name = model_name
        self._tokenizer = None
        self._model = None

    def _load(self) -> tuple[Any, Any]:
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model

        if AutoTokenizer is None or AutoModelForCausalLM is None:
            raise RuntimeError("transformers is not available")

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
        return self._tokenizer, self._model

    def generate(self, prompt: str, max_new_tokens: int = 220) -> str:
        try:
            tokenizer, model = self._load()
            inputs = tokenizer(prompt, return_tensors="pt")
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=0.0,
                top_p=1.0,
            )
            text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
            if text.startswith(prompt):
                return text[len(prompt) :].strip()
            return text.strip()
        except Exception:
            return ""


class ProjectBriefingAgent:
    """Generate concise, executive project briefs from graph state."""

    def __init__(self, llm: TextLLM | None = None) -> None:
        self._llm = llm or HuggingFaceLocalLLM()

    def _decision_matches_project(self, graph: nx.DiGraph, decision_node: str, project_id: str) -> bool:
        attrs = graph.nodes[decision_node]

        if attrs.get("project_id") == project_id:
            return True

        scoped_projects = attrs.get("scoped_projects")
        if isinstance(scoped_projects, list) and project_id in scoped_projects:
            return True

        for src, _, edge_data in graph.in_edges(decision_node, data=True):
            if edge_data.get("type") not in {"belongs_to", "in_project", "scoped_to"}:
                continue
            src_attrs = graph.nodes[src]
            if src_attrs.get("type") == "project" and src_attrs.get("project_id") == project_id:
                return True

        return False

    def _collect_project_decisions(self, graph: nx.DiGraph, project_id: str) -> list[str]:
        all_decisions = [
            node_id
            for node_id, attrs in graph.nodes(data=True)
            if attrs.get("type") == "decision"
        ]

        scoped = [
            node_id
            for node_id in all_decisions
            if self._decision_matches_project(graph, node_id, project_id)
        ]

        return scoped if scoped else all_decisions

    def _collect_active_decisions(
        self,
        graph: nx.DiGraph,
        decision_nodes: list[str],
    ) -> tuple[list[dict[str, str]], dict[str, str]]:
        active: list[dict[str, str]] = []
        latest_version_by_decision: dict[str, str] = {}

        for decision_node in decision_nodes:
            decision_id = graph.nodes[decision_node].get("decision_id")
            title = graph.nodes[decision_node].get("title") or decision_id or decision_node
            if not decision_id:
                continue

            try:
                latest_node = get_latest_decision_version(graph, decision_id)
                latest_version = graph.nodes[latest_node].get("version_id") or latest_node
            except ValueError:
                continue

            active.append(
                {
                    "decision_id": str(decision_id),
                    "title": str(title),
                    "latest_version": str(latest_version),
                }
            )
            latest_version_by_decision[str(decision_id)] = str(latest_version)

        return active, latest_version_by_decision

    def _collect_drift_signals(
        self,
        graph: nx.DiGraph,
        active_decisions: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        for decision in active_decisions:
            decision_id = decision["decision_id"]
            drift = detect_decision_drift(graph, decision_id)
            explanation = generate_drift_explanation(graph, decision_id)
            out_of_sync = explanation.get("out_of_sync_stakeholders", [])

            signals.append(
                {
                    "decision_id": decision_id,
                    "title": decision["title"],
                    "latest_version": decision["latest_version"],
                    "drift_detected": bool(drift.get("drift_detected", False)),
                    "out_of_sync_count": len(out_of_sync) if isinstance(out_of_sync, list) else 0,
                    "explanation": str(explanation.get("explanation", "")),
                }
            )

        return signals

    def _collect_affected_departments(
        self,
        graph: nx.DiGraph,
        decision_nodes: list[str],
        latest_version_by_decision: dict[str, str],
    ) -> list[str]:
        departments: set[str] = set()

        latest_version_nodes = {
            f"decision_version:{version_id}"
            for version_id in latest_version_by_decision.values()
        }

        for decision_node in decision_nodes:
            for _, stakeholder_node, edge_data in graph.out_edges(decision_node, data=True):
                if edge_data.get("type") != "affects":
                    continue
                stakeholder = graph.nodes[stakeholder_node]
                if stakeholder.get("type") != "stakeholder":
                    continue
                department = stakeholder.get("department")
                if isinstance(department, str) and department.strip():
                    departments.add(department.strip())

        for version_node in latest_version_nodes:
            if version_node not in graph:
                continue
            for stakeholder_node, _, edge_data in graph.in_edges(version_node, data=True):
                if edge_data.get("type") not in {"affected_by", "informed_of"}:
                    continue
                stakeholder = graph.nodes[stakeholder_node]
                if stakeholder.get("type") != "stakeholder":
                    continue
                department = stakeholder.get("department")
                if isinstance(department, str) and department.strip():
                    departments.add(department.strip())

        return sorted(departments)

    def _build_prompt(
        self,
        project_id: str,
        active_decisions: list[dict[str, str]],
        drift_signals: list[dict[str, Any]],
        affected_departments: list[str],
    ) -> str:
        payload = {
            "project_id": project_id,
            "active_decisions": active_decisions,
            "drift_signals": drift_signals,
            "affected_departments": affected_departments,
        }

        instructions = (
            "You are an AI Chief of Staff writing a project brief for an executive.\n"
            "Write a concise update in 5 to 6 sentences maximum.\n"
            "Focus on what changed recently, where alignment is breaking, and what matters now.\n"
            "Use plain business language. Avoid technical jargon.\n"
            "Do not list raw fields or bullet points.\n"
            "Do not invent facts beyond the provided project snapshot.\n"
        )

        return f"{instructions}\nProject snapshot:\n{json.dumps(payload, ensure_ascii=True)}\n\nBrief:"

    def _normalize_brief(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return cleaned

        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        parts = [part.strip() for part in parts if part.strip()]

        if len(parts) > 6:
            parts = parts[:6]

        return " ".join(parts)

    def _fallback_brief(
        self,
        project_id: str,
        active_decisions: list[dict[str, str]],
        drift_signals: list[dict[str, Any]],
        affected_departments: list[str],
    ) -> str:
        drifted = [signal for signal in drift_signals if signal.get("drift_detected")]

        if not active_decisions:
            return (
                f"Project {project_id} has no active decision history in the current graph snapshot. "
                "Priority should be to confirm the current decision baseline before planning next actions."
            )

        decision_count = len(active_decisions)
        drift_count = len(drifted)
        top_drift = sorted(
            drifted,
            key=lambda item: int(item.get("out_of_sync_count", 0)),
            reverse=True,
        )

        sentence_one = (
            f"Project {project_id} currently tracks {decision_count} active decisions, "
            f"with {drift_count} showing alignment drift."
        )

        if top_drift:
            lead = top_drift[0]
            sentence_two = (
                f"The most urgent risk is around {lead.get('title', lead.get('decision_id', 'a key decision'))}, "
                f"where {lead.get('out_of_sync_count', 0)} stakeholders are not aligned to the latest version."
            )
        else:
            sentence_two = (
                "Recent decision updates are broadly aligned, with no clear cross-team drift signal at this time."
            )

        if affected_departments:
            sentence_three = (
                "Departments with current impact exposure include "
                f"{', '.join(affected_departments)}."
            )
        else:
            sentence_three = "No explicit department impact links are recorded in the current graph snapshot."

        sentence_four = (
            "Near-term focus should be on confirming understanding of recent decision changes "
            "and closing gaps where teams are referencing outdated guidance."
        )

        return " ".join([sentence_one, sentence_two, sentence_three, sentence_four])

    def generate_brief(self, graph: nx.DiGraph, project_id: str) -> dict:
        """
        Generate a concise, executive project brief from graph state.

        The method is stateless and read-only: it extracts project signals,
        prompts the local LLM, and returns text with an ISO UTC timestamp.
        """
        decision_nodes = self._collect_project_decisions(graph, project_id)
        active_decisions, latest_version_by_decision = self._collect_active_decisions(
            graph, decision_nodes
        )
        drift_signals = self._collect_drift_signals(graph, active_decisions)
        affected_departments = self._collect_affected_departments(
            graph, decision_nodes, latest_version_by_decision
        )

        prompt = self._build_prompt(
            project_id=project_id,
            active_decisions=active_decisions,
            drift_signals=drift_signals,
            affected_departments=affected_departments,
        )

        generated = self._normalize_brief(self._llm.generate(prompt))
        if not generated:
            generated = self._fallback_brief(
                project_id=project_id,
                active_decisions=active_decisions,
                drift_signals=drift_signals,
                affected_departments=affected_departments,
            )

        return {
            "project_id": project_id,
            "brief_text": generated,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
