"""
Query endpoint wiring.

Accepts user input, gathers tool metadata, and delegates to the orchestrator
agent for planning. Tool execution is intentionally out of scope here.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..orchestrator.agent import Plan, draft_plan
from ..schemas.tools import ToolSpec
from ..tools.executor import ExecutionSummary, execute_plan
from ..tools.registry import list_tool_specs

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """User message payload."""

    message: str = Field(..., description="Raw user input to route through tools")


class ToolCallSpec(BaseModel):
    """Mirror of the orchestrator's tool call structure for API responses."""

    tool_name: str
    rationale: str
    input_example: dict


class QueryResponse(BaseModel):
    """Structured response exposing the plan and catalog for traceability."""

    request_id: str
    agent_plan: List[ToolCallSpec]
    tool_results: List[ExecutionSummary.model_fields["results"].annotation.__args__[0]]  # type: ignore
    available_tools: List[ToolSpec]
    notes: str | None = None


def _get_tools() -> List[ToolSpec]:
    """Dependency to fetch the current tool catalog."""

    return list_tool_specs()


@router.post("/", response_model=QueryResponse)
def route_query(payload: QueryRequest, tools: List[ToolSpec] = Depends(_get_tools)) -> QueryResponse:
    """
    Route a user query to the orchestrator agent.

    The agent returns a plan of tool calls, which is echoed back along with the
    current tool catalog. No tool execution occurs in this path.
    """

    plan: Plan = draft_plan(payload.message, tools)
    execution: ExecutionSummary = execute_plan(plan)

    return QueryResponse(
        request_id=str(uuid.uuid4()),
        agent_plan=[ToolCallSpec(**tc.dict()) for tc in plan.tool_calls],
        tool_results=execution.results,
        available_tools=tools,
        notes=plan.notes,
    )
