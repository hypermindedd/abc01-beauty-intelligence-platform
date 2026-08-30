from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from abc_core.audit.events import MutationEvent
from .enums import ActorType, EvidenceClass, PreviewStatus, RecommendationRole, SafetyTier, ServiceDecisionStatus, SpecialistValidationStatus


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ActorContext(FrozenModel):
    actor_type: ActorType
    actor_id: str
    tenant_id: str


class RequestState(FrozenModel):
    request_id: str
    service_ids: tuple[str, ...] = ()
    fixed_choice: bool = False


class ParticipantContext(FrozenModel):
    context_id: str
    explicit_preferences: tuple[str, ...] = ()
    explicit_event_context: str | None = None


class InputAsset(FrozenModel):
    asset_id: str
    media_type: str
    source_reality_note: str | None = None


class EvidenceItem(FrozenModel):
    evidence_id: str
    evidence_class: EvidenceClass
    statement: str


class EvidenceSet(FrozenModel):
    items: tuple[EvidenceItem, ...] = ()


class AnalysisState(FrozenModel):
    analysis_id: str
    summary: str = ""
    reviewed_by_specialist: bool = False
    reviewer_actor_id: str | None = None


class RecommendationOption(FrozenModel):
    option_id: str
    title: str
    role: RecommendationRole | None = None
    is_explore: bool = False


class RecommendationSet(FrozenModel):
    recommendation_set_id: str
    core_options: tuple[RecommendationOption, ...]
    explore_options: tuple[RecommendationOption, ...] = ()

    @property
    def active_count(self) -> int:
        return len(self.core_options) + len(self.explore_options)


class LookContext(FrozenModel):
    context_id: str
    explicit_intents: tuple[str, ...] = ()


class ExploreDirection(FrozenModel):
    direction_id: str
    axis: str
    option_id: str


class VisualExplorationSet(FrozenModel):
    exploration_set_id: str
    directions: tuple[ExploreDirection, ...] = ()


class MixMatchComposition(FrozenModel):
    composition_id: str
    component_option_ids: tuple[str, ...]
    compatibility_validated: bool = False


class PreviewRevision(FrozenModel):
    revision_id: str
    source_asset_id: str
    option_id: str
    status: PreviewStatus
    qa_approved: bool = False


class DecisionPreview(FrozenModel):
    preview_id: str
    revisions: tuple[PreviewRevision, ...] = ()


class ClientSelection(FrozenModel):
    selection_id: str
    option_id: str


class SpecialistValidation(FrozenModel):
    validation_id: str
    status: SpecialistValidationStatus = SpecialistValidationStatus.NOT_REVIEWED
    specialist_actor_id: str | None = None
    note: str = ""


class SafetyFlag(FrozenModel):
    flag_id: str
    tier: SafetyTier
    reason: str
    resolved: bool = False
    resolution_note: str | None = None


class ServiceDecision(FrozenModel):
    decision_id: str
    status: ServiceDecisionStatus
    note: str = ""


class FinalLookBoard(FrozenModel):
    board_id: str
    selected_option_ids: tuple[str, ...]
    presentation_only: bool = True


class SalonSessionState(FrozenModel):
    tenant_id: str
    session_id: str
    revision: int = 0
    request: RequestState | None = None
    participant_context: ParticipantContext | None = None
    input_assets: tuple[InputAsset, ...] = ()
    evidence_set: EvidenceSet = Field(default_factory=EvidenceSet)
    analysis: AnalysisState | None = None
    recommendations: RecommendationSet | None = None
    look_context: LookContext | None = None
    exploration_set: VisualExplorationSet | None = None
    mix_match: MixMatchComposition | None = None
    preview: DecisionPreview | None = None
    client_selection: ClientSelection | None = None
    specialist_validation: SpecialistValidation | None = None
    safety_flags: tuple[SafetyFlag, ...] = ()
    service_decision: ServiceDecision | None = None
    final_look_board: FinalLookBoard | None = None
    commercial_offer_ids: tuple[str, ...] = ()
    audit_events: tuple[MutationEvent, ...] = ()

    def public_snapshot(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
