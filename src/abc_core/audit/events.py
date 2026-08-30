from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from abc_core.state.enums import ActorType


class MutationEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: f"EVT-{uuid4()}")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    session_id: str
    actor_type: ActorType
    actor_id: str
    action: str
    from_revision: int
    to_revision: int
    detail: str = ""
