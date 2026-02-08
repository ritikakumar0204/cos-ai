"""
Tool execution layer.

Consumes a structured plan and executes tools deterministically. No planning or
LLM logic lives here. The executor resolves tools via the registry, runs them
in order, and returns structured results aligned with the input plan.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from ..orchestrator.agent import Plan, ToolCall
from .base import Tool, ToolError
from .registry import get_tool


class ToolResult(BaseModel):
    """Structured output for a single tool call."""

    tool_name: str
    success: bool
    output: dict | None = None
    error: str | None = None
    rationale: str | None = None


class ExecutionSummary(BaseModel):
    """Aggregate results for a plan execution."""

    results: List[ToolResult]


def _execute_call(call: ToolCall) -> ToolResult:
    """
    Execute a single tool call.

    If the tool is missing, return a stubbed failure result instead of raising.
    """

    try:
        tool: Tool = get_tool(call.tool_name)
    except KeyError:
        return ToolResult(
            tool_name=call.tool_name,
            success=False,
            output=None,
            error=f"Tool '{call.tool_name}' is not registered.",
            rationale=call.rationale,
        )

    try:
        output_model = tool.run(tool.input_model(**call.input_example))
        return ToolResult(
            tool_name=call.tool_name,
            success=True,
            output=output_model.model_dump(),
            error=None,
            rationale=call.rationale,
        )
    except ToolError as exc:
        return ToolResult(
            tool_name=call.tool_name,
            success=False,
            output=None,
            error=str(exc),
            rationale=call.rationale,
        )


def execute_plan(plan: Plan) -> ExecutionSummary:
    """
    Execute tool calls in the order provided by the plan.

    The function is synchronous and side-effect free beyond the tools'
    deterministic behavior. No retries or parallelism are introduced here.
    """

    results = [_execute_call(call) for call in plan.tool_calls]
    return ExecutionSummary(results=results)
