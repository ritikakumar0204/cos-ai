"""
In-memory tool registry.

Responsible for declaring available tools and exposing their structured
metadata. Orchestrator code should depend on this registry instead of
hard-coding tool references.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from .base import Tool
from ..schemas.tools import ToolSpec, build_tool_spec

# Internal storage keyed by tool name.
_registry: Dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    """
    Add a tool to the registry.

    Enforces unique names to keep routing deterministic. Tools should be
    registered during application startup, not at call time.
    """

    if tool.name in _registry:
        raise ValueError(f"Tool '{tool.name}' is already registered.")
    _registry[tool.name] = tool


def get_tool(name: str) -> Tool:
    """
    Retrieve a tool by name.

    Intended for orchestrator use when selecting tools based on model output.
    """

    try:
        return _registry[name]
    except KeyError as exc:
        raise KeyError(f"Tool '{name}' is not registered.") from exc


def list_tool_specs() -> List[ToolSpec]:
    """
    Return structured metadata for all registered tools.

    This data can be exposed via API to synchronize tool definitions with
    frontends and to aid tracing.
    """

    return [build_tool_spec(tool) for tool in _registry.values()]


def clear_registry() -> None:
    """
    Remove all registered tools.

    Useful for isolated tests; avoid calling in production flows.
    """

    _registry.clear()


def iter_tools() -> Iterable[Tool]:
    """Yield registered tool instances."""

    return _registry.values()
