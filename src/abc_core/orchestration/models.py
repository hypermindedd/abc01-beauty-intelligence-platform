from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class WorkflowPhase(StrEnum):
    SPECIALIST_SETUP = "SPECIALIST_SETUP"
    CLIENT_GUIDED_INPUT = "CLIENT_GUIDED_INPUT"
    ANALYSIS_REVIEW = "ANALYSIS_REVIEW"
    SHARED_REVIEW = "SHARED_REVIEW"
    SPECIALIST_VALIDATION = "SPECIALIST_VALIDATION"
    SERVICE_CONFIRMATION = "SERVICE_CONFIRMATION"
    COMPLETE = "COMPLETE"


class WorkflowSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    session_id: str
    revision: int
    phase: WorkflowPhase
    allowed_agent_ids: tuple[str, ...]
    next_actions: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    terminal: bool = False
