from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..agents.briefing_agent import ProjectBriefingAgent
from ..agents.coordinator_agent import CoordinatorAgent
from ..agents.critic_agent import CriticAgent
from ..agents.memory_agent import MemoryAgent


class MeetingParticipant(BaseModel):
    """Participant payload for meeting ingestion."""

    stakeholder_id: str
    name: str
    department: str
    role: str


class MeetingDecision(BaseModel):
    """Decision payload extracted from a meeting."""

    decision_id: str
    title: str
    version_id: str
    content: str
    confidence: float = 0.75
    reasoning: str = "Captured from meeting"


class ProcessMeetingInput(BaseModel):
    """Input schema for meeting->graph updates."""

    project_id: str = Field(..., description="Project identifier")
    meeting_id: str
    title: str
    summary: str = ""
    participants: list[MeetingParticipant] = Field(default_factory=list)
    decisions: list[MeetingDecision] = Field(default_factory=list)


class ProcessMeetingOutput(BaseModel):
    """Output schema for meeting->graph updates."""

    project_id: str
    updated_decisions: list[dict[str, str]]
    routing: dict[str, dict[str, list[str]]]
    event: dict[str, Any]


class ProcessMeetingTool:
    """Update project memory from meeting outcomes and compute routing."""

    name = "process_meeting_update"
    description = "Ingest meeting outcomes, update decision graph, and return routing targets."
    input_model = ProcessMeetingInput
    output_model = ProcessMeetingOutput

    def __init__(self) -> None:
        self._memory = MemoryAgent()

    def run(self, input_data: ProcessMeetingInput) -> ProcessMeetingOutput:
        result = self._memory.process_meeting(
            project_id=input_data.project_id,
            meeting_id=input_data.meeting_id,
            title=input_data.title,
            summary=input_data.summary,
            decisions=[item.model_dump() for item in input_data.decisions],
            participants=[item.model_dump() for item in input_data.participants],
        )
        return ProcessMeetingOutput(project_id=input_data.project_id, **result)


class StakeholderRecord(BaseModel):
    """Stakeholder payload used for routing-aware decision updates."""

    stakeholder_id: str
    name: str
    department: str
    role: str


class StampDecisionInput(BaseModel):
    """Input schema for decision version stamping."""

    project_id: str
    decision_id: str
    title: str
    version_id: str
    content: str
    confidence: float = 0.8
    reasoning: str = "Decision update"
    stakeholders: list[StakeholderRecord] = Field(default_factory=list)


class StampDecisionOutput(BaseModel):
    """Output schema for decision version stamping."""

    project_id: str
    decision_id: str
    latest_version: str
    routing: dict[str, list[str]]
    event: dict[str, Any]


class StampDecisionAndRouteTool:
    """Version-stamp a decision and compute stakeholder routing outcomes."""

    name = "stamp_decision_and_route"
    description = "Add a decision version and compute amplify/inform/restrict routing groups."
    input_model = StampDecisionInput
    output_model = StampDecisionOutput

    def __init__(self) -> None:
        self._memory = MemoryAgent()

    def run(self, input_data: StampDecisionInput) -> StampDecisionOutput:
        result = self._memory.stamp_decision_and_route(
            project_id=input_data.project_id,
            decision_id=input_data.decision_id,
            title=input_data.title,
            version_id=input_data.version_id,
            content=input_data.content,
            confidence=input_data.confidence,
            reasoning=input_data.reasoning,
            stakeholders=[item.model_dump() for item in input_data.stakeholders],
        )
        return StampDecisionOutput(project_id=input_data.project_id, **result)


class ChangedTodayInput(BaseModel):
    """Input schema for project update timelines."""

    project_id: str
    date: str | None = None


class ChangedTodayOutput(BaseModel):
    """Output schema containing updates and visual map payload."""

    project_id: str
    date: str
    updates: list[dict[str, Any]]
    visual_map: dict[str, Any]
    coordinator_summary: str | None = None


class WhatChangedTodayTool:
    """Return timeline updates plus graph map data for visualization."""

    name = "what_changed_today"
    description = "Return today's project updates and a visual graph map payload."
    input_model = ChangedTodayInput
    output_model = ChangedTodayOutput

    def __init__(self) -> None:
        self._coordinator = CoordinatorAgent()

    def run(self, input_data: ChangedTodayInput) -> ChangedTodayOutput:
        result = self._coordinator.changed_today(input_data.project_id, input_data.date)
        return ChangedTodayOutput(**result)


class AddStakeholderInput(BaseModel):
    """Input schema for stakeholder onboarding and context generation."""

    project_id: str
    stakeholder_id: str
    name: str
    department: str
    role: str


class AddStakeholderOutput(BaseModel):
    """Output schema for stakeholder context payload."""

    project_id: str
    stakeholder_id: str
    event: dict[str, Any]
    context: dict[str, Any]


class AddStakeholderContextTool:
    """Create stakeholder records and return immediate context view."""

    name = "add_stakeholder_context"
    description = "Add a stakeholder and return an instant context view for the project."
    input_model = AddStakeholderInput
    output_model = AddStakeholderOutput

    def __init__(self) -> None:
        self._memory = MemoryAgent()
        self._coordinator = CoordinatorAgent()

    def run(self, input_data: AddStakeholderInput) -> AddStakeholderOutput:
        update_result = self._memory.add_stakeholder_and_context(
            project_id=input_data.project_id,
            stakeholder={
                "stakeholder_id": input_data.stakeholder_id,
                "name": input_data.name,
                "department": input_data.department,
                "role": input_data.role,
            },
        )
        context = self._coordinator.stakeholder_context(
            project_id=input_data.project_id,
            stakeholder_id=input_data.stakeholder_id,
        )
        return AddStakeholderOutput(
            project_id=input_data.project_id,
            stakeholder_id=input_data.stakeholder_id,
            event=update_result["event"],
            context=context,
        )


class ConflictReviewInput(BaseModel):
    """Input schema for critic conflict scans."""

    project_id: str


class ConflictReviewOutput(BaseModel):
    """Output schema for critic conflict scans."""

    project_id: str
    conflicts_detected: bool
    conflict_count: int
    findings: list[dict[str, Any]]
    event: dict[str, Any]


class DetectConflictsTool:
    """Flag conflicting information for review."""

    name = "detect_conflicts_for_review"
    description = "Scan project graph for alignment/version conflicts and flag them for review."
    input_model = ConflictReviewInput
    output_model = ConflictReviewOutput

    def __init__(self) -> None:
        self._critic = CriticAgent()

    def run(self, input_data: ConflictReviewInput) -> ConflictReviewOutput:
        result = self._critic.detect_conflicts(input_data.project_id)
        return ConflictReviewOutput(**result)


class ProjectBriefInput(BaseModel):
    """Input schema for executive project brief generation."""

    project_id: str


class ProjectBriefOutput(BaseModel):
    """Output schema for executive brief generation."""

    project_id: str
    brief_text: str
    generated_at: str


class GenerateProjectBriefTool:
    """Generate a concise project AI brief from current graph signals."""

    name = "generate_project_brief"
    description = "Generate a concise chief-of-staff style project brief from graph state."
    input_model = ProjectBriefInput
    output_model = ProjectBriefOutput

    def __init__(self) -> None:
        self._agent = ProjectBriefingAgent()

    def run(self, input_data: ProjectBriefInput) -> ProjectBriefOutput:
        from ..models.org_memory import get_project_graph

        graph = get_project_graph(input_data.project_id)
        result = self._agent.generate_brief(graph=graph, project_id=input_data.project_id)
        return ProjectBriefOutput(**result)


def build_org_intelligence_tools() -> list[Any]:
    """Return all MCP-style organization intelligence tools."""
    return [
        ProcessMeetingTool(),
        StampDecisionAndRouteTool(),
        WhatChangedTodayTool(),
        AddStakeholderContextTool(),
        DetectConflictsTool(),
        GenerateProjectBriefTool(),
    ]
