from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class OrchestrationEventType(StrEnum):
    PHASE_PROJECTED = "PHASE_PROJECTED"
    AGENT_ALLOWED = "AGENT_ALLOWED"
    AGENT_REJECTED = "AGENT_REJECTED"
    IDEMPOTENCY_ACCEPTED = "IDEMPOTENCY_ACCEPTED"
    IDEMPOTENCY_REPLAY = "IDEMPOTENCY_REPLAY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"


class OrchestrationEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(default_factory=lambda: f"ORCH-{uuid4()}")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    session_id: str
    revision: int
    event_type: OrchestrationEventType
    phase: str
    agent_id: str | None = None
    idempotency_key: str | None = None
    detail: str = ""


class EventSink(Protocol):
    def emit(self, event: OrchestrationEvent) -> None: ...


class InMemoryEventSink:
    """Engineering-only sink. R02.4 owns durable observability adapter boundaries."""

    def __init__(self) -> None:
        self._events: list[OrchestrationEvent] = []

    def emit(self, event: OrchestrationEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[OrchestrationEvent, ...]:
        return tuple(self._events)
