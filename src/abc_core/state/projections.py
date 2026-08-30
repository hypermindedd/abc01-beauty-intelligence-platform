from __future__ import annotations

from typing import Iterable

from .enums import ActorType
from .models import ActorContext, SalonSessionState


def compile_output_projection(state: SalonSessionState, actor: ActorContext, output_ids: Iterable[str] | None = None) -> dict:
    if actor.tenant_id != state.tenant_id:
        raise ValueError("tenant mismatch")
    if actor.actor_type is not ActorType.OUTPUT_COMPILER:
        raise ValueError("only OUTPUT_COMPILER may compile projections")
    selected = tuple(output_ids) if output_ids is not None else state.output_selection.output_ids
    # Projection-only by contract: this function does not return a new canonical state and never increments revision.
    return {
        "session_id": state.session_id,
        "state_revision": state.revision,
        "output_ids": selected,
        "client_selection": state.client_selection.model_dump(mode="json") if state.client_selection else None,
        "service_decision": state.service_decision.model_dump(mode="json") if state.service_decision else None,
        "safety_flags": [f.model_dump(mode="json") for f in state.safety_flags],
        "read_only_projection": True,
    }
