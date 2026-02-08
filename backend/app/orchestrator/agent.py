"""
LLM-facing orchestrator agent.

The agent's sole job is to interpret user intent and propose which tools to
call next. It does not execute tools or embed business logic. The output is a
structured plan that downstream components can execute and trace.
"""

from __future__ import annotations

import json
import re
from typing import List, Protocol

from pydantic import BaseModel

from ..schemas.tools import ToolSpec
from .prompts import build_system_prompt

try:
    from ..agents.briefing_agent import HuggingFaceLocalLLM
except Exception:  # pragma: no cover
    HuggingFaceLocalLLM = None  # type: ignore[assignment]


class ToolCall(BaseModel):
    """Structured description of a proposed tool invocation."""

    tool_name: str
    rationale: str
    input_example: dict


class Plan(BaseModel):
    """
    Plan returned by the agent.

    Contains the ordered list of tool calls the orchestrator should execute.
    No execution occurs here; the caller decides how to handle the plan.
    """

    tool_calls: List[ToolCall]
    notes: str | None = None


class PlannerLLM(Protocol):
    """Interface for LLM-based orchestrator planning."""

    def generate(self, prompt: str, max_new_tokens: int = 220) -> str:
        """Generate text output for a planning prompt."""


_PROJECT_RE = re.compile(r"\bproj-\d+\b", re.IGNORECASE)
_DECISION_RE = re.compile(r"\bdec-\d+\b", re.IGNORECASE)
_STAKEHOLDER_RE = re.compile(r"\bs-\d+\b", re.IGNORECASE)
_PLANNER_LLM: PlannerLLM | None = None
_PLANNER_LLM_INIT_ATTEMPTED = False


def _extract(pattern: re.Pattern[str], text: str, default: str) -> str:
    match = pattern.search(text)
    return match.group(0).lower() if match else default


def _supports(tool_name: str, available: set[str]) -> bool:
    return tool_name in available


def _planner_llm() -> PlannerLLM | None:
    global _PLANNER_LLM, _PLANNER_LLM_INIT_ATTEMPTED
    if _PLANNER_LLM_INIT_ATTEMPTED:
        return _PLANNER_LLM

    _PLANNER_LLM_INIT_ATTEMPTED = True
    if HuggingFaceLocalLLM is None:
        return None

    try:
        _PLANNER_LLM = HuggingFaceLocalLLM()
    except Exception:
        _PLANNER_LLM = None
    return _PLANNER_LLM


def _tool_input_template(
    tool_name: str,
    user_message: str,
    project_id: str,
    decision_id: str,
    stakeholder_id: str,
) -> dict:
    if tool_name == "process_meeting_update":
        return {
            "project_id": project_id,
            "meeting_id": "mtg-auto-1",
            "title": "Captured meeting update",
            "summary": user_message,
            "participants": [
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
                {
                    "stakeholder_id": "s-3",
                    "name": "Carol",
                    "department": "Operations",
                    "role": "Affected",
                },
            ],
            "decisions": [
                {
                    "decision_id": decision_id,
                    "title": "Meeting-derived decision update",
                    "version_id": "v-auto-1",
                    "content": "Decision update captured from meeting.",
                    "confidence": 0.8,
                    "reasoning": "Derived from meeting summary.",
                }
            ],
        }

    if tool_name == "stamp_decision_and_route":
        return {
            "project_id": project_id,
            "decision_id": decision_id,
            "title": "Decision update",
            "version_id": "v-auto-1",
            "content": "Updated decision content.",
            "confidence": 0.85,
            "reasoning": "User-requested decision update.",
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
                {
                    "stakeholder_id": "s-3",
                    "name": "Carol",
                    "department": "Operations",
                    "role": "Affected",
                },
            ],
        }

    if tool_name == "what_changed_today":
        return {"project_id": project_id}

    if tool_name == "add_stakeholder_context":
        return {
            "project_id": project_id,
            "stakeholder_id": stakeholder_id,
            "name": "New Stakeholder",
            "department": "Operations",
            "role": "Informed",
        }

    if tool_name == "detect_conflicts_for_review":
        return {"project_id": project_id}

    if tool_name == "generate_project_brief":
        return {"project_id": project_id}

    return {}


def _extract_json_object(text: str) -> dict | None:
    candidate = text.strip()
    if not candidate:
        return None
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        payload = json.loads(candidate[start : end + 1])
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _draft_plan_deterministic(user_message: str, tools: List[ToolSpec]) -> Plan:
    lower = user_message.lower()
    available = {tool.name for tool in tools}
    project_id = _extract(_PROJECT_RE, user_message, "proj-1")
    decision_id = _extract(_DECISION_RE, user_message, "dec-1")
    stakeholder_id = _extract(_STAKEHOLDER_RE, user_message, "s-1")
    tool_calls: list[ToolCall] = []

    if any(token in lower for token in ["meeting", "sync ended", "meeting ended", "minutes"]):
        if _supports("process_meeting_update", available):
            tool_calls.append(
                ToolCall(
                    tool_name="process_meeting_update",
                    rationale="Meeting outcomes should update memory and routing.",
                    input_example=_tool_input_template(
                        "process_meeting_update",
                        user_message,
                        project_id,
                        decision_id,
                        stakeholder_id,
                    ),
                )
            )

    elif any(token in lower for token in ["decision", "version", "route", "affected teams"]):
        if _supports("stamp_decision_and_route", available):
            tool_calls.append(
                ToolCall(
                    tool_name="stamp_decision_and_route",
                    rationale="Decision change should be version-stamped and routed.",
                    input_example=_tool_input_template(
                        "stamp_decision_and_route",
                        user_message,
                        project_id,
                        decision_id,
                        stakeholder_id,
                    ),
                )
            )

    elif any(token in lower for token in ["what changed", "today", "updates", "visual map", "map of updates"]):
        if _supports("what_changed_today", available):
            tool_calls.append(
                ToolCall(
                    tool_name="what_changed_today",
                    rationale="User requested daily updates and a visualizable map payload.",
                    input_example=_tool_input_template(
                        "what_changed_today",
                        user_message,
                        project_id,
                        decision_id,
                        stakeholder_id,
                    ),
                )
            )

    elif any(token in lower for token in ["new stakeholder", "joins", "onboard", "context view"]):
        if _supports("add_stakeholder_context", available):
            tool_calls.append(
                ToolCall(
                    tool_name="add_stakeholder_context",
                    rationale="New stakeholder onboarding should create context immediately.",
                    input_example=_tool_input_template(
                        "add_stakeholder_context",
                        user_message,
                        project_id,
                        decision_id,
                        stakeholder_id,
                    ),
                )
            )

    elif any(token in lower for token in ["conflict", "contradiction", "critic", "deconflict"]):
        if _supports("detect_conflicts_for_review", available):
            tool_calls.append(
                ToolCall(
                    tool_name="detect_conflicts_for_review",
                    rationale="Contradictions should be flagged by critic workflow.",
                    input_example=_tool_input_template(
                        "detect_conflicts_for_review",
                        user_message,
                        project_id,
                        decision_id,
                        stakeholder_id,
                    ),
                )
            )

    if not tool_calls and _supports("generate_project_brief", available):
        tool_calls.append(
            ToolCall(
                tool_name="generate_project_brief",
                rationale="Default to a concise project AI brief when intent is general.",
                input_example=_tool_input_template(
                    "generate_project_brief",
                    user_message,
                    project_id,
                    decision_id,
                    stakeholder_id,
                ),
            )
        )

    return Plan(
        tool_calls=tool_calls,
        notes="Deterministic intent routing applied. Replace with full LLM planner later if needed.",
    )


def _draft_plan_llm(user_message: str, tools: List[ToolSpec]) -> Plan | None:
    llm = _planner_llm()
    if llm is None:
        return None

    system_prompt = build_system_prompt(tools)
    available = {tool.name for tool in tools}
    project_id = _extract(_PROJECT_RE, user_message, "proj-1")
    decision_id = _extract(_DECISION_RE, user_message, "dec-1")
    stakeholder_id = _extract(_STAKEHOLDER_RE, user_message, "s-1")

    deterministic = _draft_plan_deterministic(user_message, tools)
    template_by_tool = {call.tool_name: call.input_example for call in deterministic.tool_calls}

    prompt = (
        f"{system_prompt}\n\n"
        "Return strict JSON object with this shape:\n"
        "{"
        "\"tool_calls\": ["
        "{\"tool_name\": \"...\", \"rationale\": \"...\", \"input_example\": {...}}"
        "]"
        "}\n"
        "Constraints:\n"
        "- Use only available tools.\n"
        "- Prefer 1-2 tool calls max.\n"
        "- Keep rationale concise.\n"
        "- If unsure, choose generate_project_brief.\n\n"
        f"user_message={user_message}\n"
        f"hints={{\"project_id\":\"{project_id}\",\"decision_id\":\"{decision_id}\",\"stakeholder_id\":\"{stakeholder_id}\"}}\n"
    )

    try:
        raw = llm.generate(prompt, max_new_tokens=220)
        parsed = _extract_json_object(raw)
        if not parsed:
            return None
        raw_calls = parsed.get("tool_calls")
        if not isinstance(raw_calls, list):
            return None

        tool_calls: list[ToolCall] = []
        for item in raw_calls:
            if not isinstance(item, dict):
                continue
            tool_name = str(item.get("tool_name", "")).strip()
            if not tool_name or not _supports(tool_name, available):
                continue

            rationale = str(item.get("rationale", "")).strip() or "LLM-selected tool for user request."
            input_example = item.get("input_example")
            if not isinstance(input_example, dict):
                input_example = template_by_tool.get(tool_name) or _tool_input_template(
                    tool_name,
                    user_message,
                    project_id,
                    decision_id,
                    stakeholder_id,
                )

            tool_calls.append(
                ToolCall(
                    tool_name=tool_name,
                    rationale=rationale,
                    input_example=input_example,
                )
            )

        if not tool_calls:
            return None

        return Plan(
            tool_calls=tool_calls,
            notes="LLM-assisted routing applied with deterministic template fallback.",
        )
    except Exception:
        return None


def draft_plan(user_message: str, tools: List[ToolSpec]) -> Plan:
    """
    Produce a tool call plan given user input and available tool metadata.

    The planner uses deterministic intent routing so the existing MCP execution
    path can be used immediately even before a full free-form LLM planner is
    introduced.
    """

    _ = build_system_prompt(tools)
    llm_plan = _draft_plan_llm(user_message, tools)
    if llm_plan is not None:
        return llm_plan
    return _draft_plan_deterministic(user_message, tools)
