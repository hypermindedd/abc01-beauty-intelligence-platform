from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abc_core.audit.events import MutationEvent
from .enums import ActorType, PreviewStatus, RecommendationRole, SafetyTier, ServiceDecisionStatus, SpecialistValidationStatus
from .models import ActorContext, AnalysisState, ClientSelection, DecisionPreview, EvidenceItem, EvidenceSet, PreviewRevision, RecommendationOption, RecommendationSet, SafetyFlag, SalonSessionState, ServiceDecision, SpecialistValidation


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

    def add_evidence(self, state: SalonSessionState, actor: ActorContext, item: EvidenceItem) -> SalonSessionState:
        items = state.evidence_set.items + (item,)
        return self._commit(state, actor, "ADD_EVIDENCE", evidence_set=EvidenceSet(items=items))

    def set_analysis(self, state: SalonSessionState, actor: ActorContext, analysis: AnalysisState) -> SalonSessionState:
        if analysis.reviewed_by_specialist:
            if actor.actor_type is not ActorType.SPECIALIST:
                raise MutationRejected("only specialist may mark analysis reviewed")
            analysis = analysis.model_copy(update={"reviewer_actor_id": actor.actor_id})
        return self._commit(state, actor, "SET_ANALYSIS", analysis=analysis)

    def publish_recommendations(self, state: SalonSessionState, actor: ActorContext, recommendations: RecommendationSet) -> SalonSessionState:
        if state.analysis is None or not state.analysis.reviewed_by_specialist:
            raise MutationRejected("ranked recommendation requires specialist-reviewed analysis")
        core = recommendations.core_options
        explore = recommendations.explore_options
        expected_roles = {RecommendationRole.BEST_FIT, RecommendationRole.ALTERNATIVE, RecommendationRole.BOLDER}
        roles = {o.role for o in core}
        if len(core) != 3 or roles != expected_roles:
            raise MutationRejected("core recommendation roles must be exactly BEST_FIT/ALTERNATIVE/BOLDER")
        if any(o.is_explore or o.role is None for o in core):
            raise MutationRejected("core options cannot be Explore options")
        if len(explore) > self.max_explore:
            raise MutationRejected("Explore exceeds 0-3 directions")
        if any((not o.is_explore) or o.role is not None for o in explore):
            raise MutationRejected("Explore directions cannot relabel core roles")
        if recommendations.active_count > self.max_active_looks:
            raise MutationRejected("active look limit exceeded")
        ids = [o.option_id for o in core + explore]
        if len(ids) != len(set(ids)):
            raise MutationRejected("duplicate recommendation option id")
        return self._commit(state, actor, "PUBLISH_RECOMMENDATIONS", recommendations=recommendations)

    def select_option(self, state: SalonSessionState, actor: ActorContext, selection: ClientSelection) -> SalonSessionState:
        if actor.actor_type not in {ActorType.CLIENT, ActorType.SPECIALIST}:
            raise MutationRejected("client selection requires client or specialist actor")
        valid_ids: set[str] = set()
        if state.recommendations:
            valid_ids = {o.option_id for o in state.recommendations.core_options + state.recommendations.explore_options}
        if selection.option_id not in valid_ids:
            raise MutationRejected("selection does not reference an active recommendation")
        return self._commit(state, actor, "CLIENT_SELECTION", client_selection=selection)

    def set_specialist_validation(self, state: SalonSessionState, actor: ActorContext, validation: SpecialistValidation) -> SalonSessionState:
        if actor.actor_type is not ActorType.SPECIALIST:
            raise MutationRejected("only specialist may mutate Specialist Validation")
        validation = validation.model_copy(update={"specialist_actor_id": actor.actor_id})
        return self._commit(state, actor, "SPECIALIST_VALIDATION", specialist_validation=validation)

    def add_safety_flag(self, state: SalonSessionState, actor: ActorContext, flag: SafetyFlag) -> SalonSessionState:
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SPECIALIST}:
            raise MutationRejected("safety mutation actor not authorized")
        if any(existing.flag_id == flag.flag_id for existing in state.safety_flags):
            raise MutationRejected("duplicate safety flag id")
        return self._commit(state, actor, "ADD_SAFETY_FLAG", safety_flags=state.safety_flags + (flag,))

    def resolve_safety_flag(self, state: SalonSessionState, actor: ActorContext, flag_id: str, note: str) -> SalonSessionState:
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
        if actor.actor_type not in {ActorType.VISUAL_RUNTIME, ActorType.SYSTEM}:
            raise MutationRejected("preview mutation actor not authorized")
        if revision.status is PreviewStatus.QA_APPROVED and not revision.qa_approved:
            raise MutationRejected("QA_APPROVED preview must carry qa_approved=true")
        current = state.preview or DecisionPreview(preview_id=f"PREVIEW-{state.session_id}")
        preview = current.model_copy(update={"revisions": current.revisions + (revision,)})
        return self._commit(state, actor, "RECORD_PREVIEW_REVISION", preview=preview)

    def set_commercial_eligibility(self, state: SalonSessionState, actor: ActorContext, offer_ids: tuple[str, ...]) -> SalonSessionState:
        if actor.actor_type not in {ActorType.SYSTEM, ActorType.SALON_ADMIN}:
            raise MutationRejected("commercial eligibility actor not authorized")
        return self._commit(state, actor, "SET_COMMERCIAL_ELIGIBILITY", commercial_offer_ids=offer_ids)

    def set_service_decision(self, state: SalonSessionState, actor: ActorContext, decision: ServiceDecision) -> SalonSessionState:
        if actor.actor_type is not ActorType.SPECIALIST:
            raise MutationRejected("service decision requires specialist actor")
        unresolved_high = [f for f in state.safety_flags if not f.resolved and f.tier in {SafetyTier.S2, SafetyTier.S3}]
        if decision.status is ServiceDecisionStatus.PROCEED:
            if state.specialist_validation is None or state.specialist_validation.status is not SpecialistValidationStatus.PASSED:
                raise MutationRejected("PROCEED requires Specialist Validation PASSED")
            if unresolved_high:
                raise MutationRejected("PROCEED blocked by unresolved S2/S3 safety state")
        return self._commit(state, actor, "SERVICE_DECISION", service_decision=decision)
