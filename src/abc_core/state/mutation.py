from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abc_core.audit.events import MutationEvent
from .enums import ActorType, PreviewStatus, RecommendationRole, SafetyTier, ServiceDecisionStatus, SpecialistValidationStatus
from .models import ActorContext, AnalysisState, ClientSelection, DecisionPreview, EvidenceItem, EvidenceSet, FinalLookBoard, InputAsset, LookContext, MixMatchComposition, OutputSelection, ParticipantContext, PreviewRevision, RecommendationSet, RequestState, SafetyFlag, SalonSessionState, ServiceDecision, SpecialistValidation, VisualExplorationSet


class MutationRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class SessionMutationEngine:
    max_active_looks: int = 6
    max_explore: int = 3

    def _guard_tenant(self, state: SalonSessionState, actor: ActorContext) -> None:
        if actor.tenant_id != state.tenant_id:
            raise MutationRejected("tenant mismatch")

    def _commit(self, state: SalonSessionState, actor: ActorContext, action: str, **updates: Any) -> SalonSessionState:
        self._guard_tenant(state, actor)
        next_revision = state.revision + 1
        event = MutationEvent(
            tenant_id=state.tenant_id,
            session_id=state.session_id,
            actor_type=actor.actor_type,
            actor_id=actor.actor_id,
            action=action,
            from_revision=state.revision,
            to_revision=next_revision,
        )
        updates["revision"] = next_revision
        updates["audit_events"] = state.audit_events + (event,)
        return state.model_copy(update=updates)

    def set_request(self, state: SalonSessionState, actor: ActorContext, request: RequestState) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SPECIALIST}:
            raise MutationRejected("request mutation actor not authorized")
        return self._commit(state, actor, "SET_REQUEST", request=request)

    def set_participant_context(self, state: SalonSessionState, actor: ActorContext, context: ParticipantContext) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST, ActorType.SYSTEM}:
            raise MutationRejected("participant context actor not authorized")
        return self._commit(state, actor, "SET_PARTICIPANT_CONTEXT", participant_context=context)

    def add_input_asset(self, state: SalonSessionState, actor: ActorContext, asset: InputAsset) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST, ActorType.SYSTEM}:
            raise MutationRejected("input asset actor not authorized")
        if any(existing.asset_id == asset.asset_id for existing in state.input_assets):
            raise MutationRejected("duplicate input asset id")
        return self._commit(state, actor, "ADD_INPUT_ASSET", input_assets=state.input_assets + (asset,))

    def add_evidence(self, state: SalonSessionState, actor: ActorContext, item: EvidenceItem) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if any(existing.evidence_id == item.evidence_id for existing in state.evidence_set.items):
            raise MutationRejected("duplicate evidence id")
        items = state.evidence_set.items + (item,)
        return self._commit(state, actor, "ADD_EVIDENCE", evidence_set=EvidenceSet(items=items))

    def set_analysis(self, state: SalonSessionState, actor: ActorContext, analysis: AnalysisState) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if analysis.reviewed_by_specialist:
            if actor.actor_type is not ActorType.SPECIALIST:
                raise MutationRejected("only specialist may mark analysis reviewed")
            analysis = analysis.model_copy(update={"reviewer_actor_id": actor.actor_id})
        return self._commit(state, actor, "SET_ANALYSIS", analysis=analysis)

    def publish_recommendations(self, state: SalonSessionState, actor: ActorContext, recommendations: RecommendationSet, *, explicit_explore_requested: bool = False) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if state.analysis is None or not state.analysis.reviewed_by_specialist:
            raise MutationRejected("ranked recommendation requires specialist-reviewed analysis")
        core = recommendations.core_options
        explore = recommendations.explore_options
        role_order = (RecommendationRole.BEST_FIT, RecommendationRole.ALTERNATIVE, RecommendationRole.BOLDER)
        if not 1 <= len(core) <= 3:
            raise MutationRejected("core recommendations must contain 1-3 valid directions; three is a maximum, not a quota")
        if tuple(option.role for option in core) != role_order[: len(core)]:
            raise MutationRejected("core roles must follow BEST_FIT then ALTERNATIVE then BOLDER without gaps")
        if any(option.is_explore or option.role is None for option in core):
            raise MutationRejected("core options cannot be Explore options")
        if len(explore) > self.max_explore:
            raise MutationRejected("Explore exceeds 0-3 directions")
        if any((not option.is_explore) or option.role is not None for option in explore):
            raise MutationRejected("Explore directions cannot relabel core roles")
        if explore and not explicit_explore_requested:
            raise MutationRejected("Explore requires explicit client or specialist request")
        if recommendations.active_count > self.max_active_looks:
            raise MutationRejected("active look limit exceeded")
        ids = [option.option_id for option in core + explore]
        if len(ids) != len(set(ids)):
            raise MutationRejected("duplicate recommendation option id")
        return self._commit(state, actor, "PUBLISH_RECOMMENDATIONS", recommendations=recommendations)

    def set_look_context(self, state: SalonSessionState, actor: ActorContext, context: LookContext) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST, ActorType.SYSTEM}:
            raise MutationRejected("look context actor not authorized")
        return self._commit(state, actor, "SET_LOOK_CONTEXT", look_context=context)

    def set_exploration_set(self, state: SalonSessionState, actor: ActorContext, exploration: VisualExplorationSet) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST}:
            raise MutationRejected("Explore must be explicitly initiated in the consultation flow")
        if len(exploration.directions) > self.max_explore:
            raise MutationRejected("Explore exceeds 0-3 directions")
        available = set()
        if state.recommendations:
            available = {option.option_id for option in state.recommendations.explore_options}
        if any(direction.option_id not in available for direction in exploration.directions):
            raise MutationRejected("Explore direction must reference an active Explore option")
        return self._commit(state, actor, "SET_EXPLORATION_SET", exploration_set=exploration)

    def set_mix_match(self, state: SalonSessionState, actor: ActorContext, composition: MixMatchComposition) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST}:
            raise MutationRejected("Mix & Match actor not authorized")
        if not composition.compatibility_validated:
            raise MutationRejected("incompatible or unvalidated Mix & Match cannot enter canonical truth")
        return self._commit(state, actor, "SET_MIX_MATCH", mix_match=composition)

    def select_option(self, state: SalonSessionState, actor: ActorContext, selection: ClientSelection) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST}:
            raise MutationRejected("client selection requires client or specialist actor")
        valid_ids: set[str] = set()
        if state.recommendations:
            valid_ids = {option.option_id for option in state.recommendations.core_options + state.recommendations.explore_options}
        if selection.option_id not in valid_ids:
            raise MutationRejected("selection does not reference an active recommendation")
        return self._commit(state, actor, "CLIENT_SELECTION", client_selection=selection)

    def set_specialist_validation(self, state: SalonSessionState, actor: ActorContext, validation: SpecialistValidation) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type is not ActorType.SPECIALIST:
            raise MutationRejected("only specialist may mutate Specialist Validation")
        validation = validation.model_copy(update={"specialist_actor_id": actor.actor_id})
        return self._commit(state, actor, "SPECIALIST_VALIDATION", specialist_validation=validation)

    def add_safety_flag(self, state: SalonSessionState, actor: ActorContext, flag: SafetyFlag) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SPECIALIST}:
            raise MutationRejected("safety mutation actor not authorized")
        if any(existing.flag_id == flag.flag_id for existing in state.safety_flags):
            raise MutationRejected("duplicate safety flag id")
        return self._commit(state, actor, "ADD_SAFETY_FLAG", safety_flags=state.safety_flags + (flag,))

    def resolve_safety_flag(self, state: SalonSessionState, actor: ActorContext, flag_id: str, note: str) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type is not ActorType.SPECIALIST:
            raise MutationRejected("only specialist may resolve professional safety flags")
        found = False
        flags: list[SafetyFlag] = []
        for flag in state.safety_flags:
            if flag.flag_id == flag_id:
                found = True
                flags.append(flag.model_copy(update={"resolved": True, "resolution_note": note}))
            else:
                flags.append(flag)
        if not found:
            raise MutationRejected("safety flag not found")
        return self._commit(state, actor, "RESOLVE_SAFETY_FLAG", safety_flags=tuple(flags))

    def record_preview_revision(self, state: SalonSessionState, actor: ActorContext, revision: PreviewRevision) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.VISUAL_RUNTIME, ActorType.SYSTEM}:
            raise MutationRejected("preview mutation actor not authorized")
        if revision.status is PreviewStatus.QA_APPROVED and not revision.qa_approved:
            raise MutationRejected("QA_APPROVED preview must carry qa_approved=true")
        current = state.preview or DecisionPreview(preview_id=f"PREVIEW-{state.session_id}")
        preview = current.model_copy(update={"revisions": current.revisions + (revision,)})
        return self._commit(state, actor, "RECORD_PREVIEW_REVISION", preview=preview)

    def set_commercial_eligibility(self, state: SalonSessionState, actor: ActorContext, offer_ids: tuple[str, ...]) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SALON_ADMIN}:
            raise MutationRejected("commercial eligibility actor not authorized")
        return self._commit(state, actor, "SET_COMMERCIAL_ELIGIBILITY", commercial_offer_ids=offer_ids)

    def set_service_decision(self, state: SalonSessionState, actor: ActorContext, decision: ServiceDecision) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type is not ActorType.SPECIALIST:
            raise MutationRejected("service decision requires specialist actor")
        unresolved_high = [flag for flag in state.safety_flags if not flag.resolved and flag.tier in {SafetyTier.S2, SafetyTier.S3}]
        if decision.status is ServiceDecisionStatus.PROCEED:
            if state.specialist_validation is None or state.specialist_validation.status is not SpecialistValidationStatus.PASSED:
                raise MutationRejected("PROCEED requires Specialist Validation PASSED")
            if unresolved_high:
                raise MutationRejected("PROCEED blocked by unresolved S2/S3 safety state")
        return self._commit(state, actor, "SERVICE_DECISION", service_decision=decision)

    def set_output_selection(self, state: SalonSessionState, actor: ActorContext, selection: OutputSelection) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SPECIALIST}:
            raise MutationRejected("output selection actor not authorized")
        return self._commit(state, actor, "SET_OUTPUT_SELECTION", output_selection=selection)

    def set_final_look_board(self, state: SalonSessionState, actor: ActorContext, board: FinalLookBoard) -> SalonSessionState:
        self._guard_tenant(state, actor)
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SPECIALIST}:
            raise MutationRejected("Final Look Board actor not authorized")
        if not board.presentation_only:
            raise MutationRejected("Final Look Board cannot become execution clearance")
        return self._commit(state, actor, "SET_FINAL_LOOK_BOARD", final_look_board=board)
