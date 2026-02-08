"""
Tool interface definition.

The LLM orchestrator should only call these tools; all deterministic logic
must be implemented behind this interface. Tools declare their schemas
explicitly so both backend and frontend can validate inputs and outputs.
"""

from __future__ import annotations

from typing import Any, Protocol, Type

from pydantic import BaseModel


class Tool(Protocol):
    """
    Minimal contract every tool must implement.

    Tools expose structured metadata and a deterministic `run` method. The
    orchestrator decides when to call a tool but never how it computes results.
    """

    name: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]

    def run(self, input_data: BaseModel) -> BaseModel:
        """
        Execute the tool deterministically.

        The `input_data` is already validated against `input_model`. Implementers
        must return an instance of `output_model` and avoid side effects that are
        not part of the declared contract.
        """

        ...


class ToolError(Exception):
    """Raised by tools when deterministic execution fails."""
