"""
MCP-style tool endpoints.

These routes expose the internal tool registry as a discoverable/invocable API
surface so external clients can use the organization-brain capabilities without
going through natural-language query routing.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from ..schemas.tools import ToolSpec
from ..tools.base import ToolError
from ..tools.registry import get_tool, list_tool_specs

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ToolInvokeResponse(BaseModel):
    """Response payload for direct tool invocation."""

    tool_name: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class MeetingEndedRequest(BaseModel):
    """Shortcut request for meeting-ended scenario."""

    project_id: str
    meeting_id: str
    title: str
    summary: str = ""
    participants: list[dict[str, str]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)


class DecisionMadeRequest(BaseModel):
    """Shortcut request for decision stamping and routing scenario."""

    project_id: str
    decision_id: str
    title: str
    version_id: str
    content: str
    confidence: float = 0.8
    reasoning: str = "Decision update"
    stakeholders: list[dict[str, str]] = Field(default_factory=list)


class ChangedTodayRequest(BaseModel):
    """Shortcut request for founder daily changes scenario."""

    project_id: str
    date: str | None = None


class StakeholderJoinedRequest(BaseModel):
    """Shortcut request for new stakeholder onboarding scenario."""

    project_id: str
    stakeholder_id: str
    name: str
    department: str
    role: str


class ConflictScanRequest(BaseModel):
    """Shortcut request for critic conflict scan scenario."""

    project_id: str


def _invoke_tool(tool_name: str, raw_input: dict[str, Any]) -> ToolInvokeResponse:
    try:
        tool = get_tool(tool_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        validated = tool.input_model(**raw_input)
        output = tool.run(validated).model_dump()
    except ToolError as exc:
        return ToolInvokeResponse(tool_name=tool_name, success=False, error=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ToolInvokeResponse(tool_name=tool_name, success=True, result=output)


@router.get("/tools", response_model=list[ToolSpec])
def mcp_list_tools() -> list[ToolSpec]:
    """Return all registered MCP-style tools and their schemas."""
    return list_tool_specs()


@router.post("/tools/{tool_name}", response_model=ToolInvokeResponse)
def mcp_invoke_tool(
    tool_name: str,
    payload: dict[str, Any] = Body(default_factory=dict),
) -> ToolInvokeResponse:
    """Invoke a registered tool by name with structured input payload."""
    return _invoke_tool(tool_name, payload)


@router.post("/scenarios/meeting-ended", response_model=ToolInvokeResponse)
def scenario_meeting_ended(payload: MeetingEndedRequest) -> ToolInvokeResponse:
    """Scenario: meeting ends -> update graph and route stakeholders."""
    return _invoke_tool("process_meeting_update", payload.model_dump())


@router.post("/scenarios/decision-made", response_model=ToolInvokeResponse)
def scenario_decision_made(payload: DecisionMadeRequest) -> ToolInvokeResponse:
    """Scenario: decision made -> version-stamp and route affected teams."""
    return _invoke_tool("stamp_decision_and_route", payload.model_dump())


@router.post("/scenarios/what-changed-today", response_model=ToolInvokeResponse)
def scenario_what_changed_today(payload: ChangedTodayRequest) -> ToolInvokeResponse:
    """Scenario: founder asks for today's changes and graph map."""
    return _invoke_tool("what_changed_today", payload.model_dump())


@router.post("/scenarios/stakeholder-joined", response_model=ToolInvokeResponse)
def scenario_stakeholder_joined(payload: StakeholderJoinedRequest) -> ToolInvokeResponse:
    """Scenario: new stakeholder joins -> build instant context view."""
    return _invoke_tool("add_stakeholder_context", payload.model_dump())


@router.post("/scenarios/scan-conflicts", response_model=ToolInvokeResponse)
def scenario_scan_conflicts(payload: ConflictScanRequest) -> ToolInvokeResponse:
    """Scenario: critic flags conflicting information for review."""
    return _invoke_tool("detect_conflicts_for_review", payload.model_dump())
