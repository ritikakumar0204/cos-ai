"""
Shared tool schemas.

Defines the structured metadata that describes a tool's contract. These
schemas are safe to expose over HTTP so frontends can dynamically align with
backend tool definitions.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from ..tools.base import Tool


class ToolSchema(BaseModel):
    """JSON schema and identifier for a Pydantic model."""

    name: str
    schema: dict[str, Any]


class ToolSpec(BaseModel):
    """Public metadata describing a tool's contract."""

    name: str
    description: str
    input_schema: ToolSchema
    output_schema: ToolSchema


def to_schema(model: Type[BaseModel]) -> ToolSchema:
    """Build a serializable schema from a Pydantic model class."""

    return ToolSchema(name=model.__name__, schema=model.model_json_schema())


def build_tool_spec(tool: Tool) -> ToolSpec:
    """
    Convert a Tool instance into its shareable specification.

    Intended for registry exports and OpenAPI exposure; avoid embedding tool
    implementations here to keep the separation of concerns clear.
    """

    return ToolSpec(
        name=tool.name,
        description=tool.description,
        input_schema=to_schema(tool.input_model),
        output_schema=to_schema(tool.output_model),
    )
