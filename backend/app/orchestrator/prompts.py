"""
Prompts for the orchestrator agent.

These strings describe how the LLM should choose tools. They intentionally
forbid free-form answers when tools are applicable, ensuring that logic remains
inside deterministic tools. Extend here as routing behavior evolves.
"""

from __future__ import annotations

from typing import List

from ..schemas.tools import ToolSpec


BASE_SYSTEM_PROMPT = """
You are a routing agent. Your responsibilities:
- Decide which registered tools to call, and in what order.
- Never perform the underlying computation yourself.
- Prefer using tools when they match the user's request.
- If no tool is suitable, state that explicitly and ask for clarification.

Rules:
- Do not answer free-form if a tool could be used.
- Do not fabricate tool names or parameters—use only the provided catalog.
- Return only structured tool call plans; no prose explanations.
""".strip()


def build_system_prompt(tools: List[ToolSpec]) -> str:
    """
    Construct the system prompt with the current tool catalog embedded.

    The embedded catalog helps the LLM stay within supported capabilities.
    """

    tool_lines = []
    for spec in tools:
        tool_lines.append(
            f"- {spec.name}: {spec.description} "
            f"(input={spec.input_schema.name}, output={spec.output_schema.name})"
        )

    catalog = "\n".join(tool_lines) if tool_lines else "- (no tools registered)"

    return f"{BASE_SYSTEM_PROMPT}\n\nAvailable tools:\n{catalog}"
