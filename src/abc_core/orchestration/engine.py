from __future__ import annotations

from dataclasses import dataclass

from abc_core.state.enums import SafetyTier, ServiceDecisionStatus, SpecialistValidationStatus
from abc_core.state.models import SalonSessionState
from .models import WorkflowPhase, WorkflowSnapshot


class OrchestrationRejected(RuntimeError):
    pass


_PHASE_AGENTS: dict[WorkflowPhase, tuple[str, ...]] = {
    WorkflowPhase.SPECIALIST_SETUP: ("AG-01", "AG-02", "AG-07", "AG-08"),
    WorkflowPhase.CLIENT_GUIDED_INPUT: ("AG-01", "AG-02", "AG-03", "AG-08"),
    WorkflowPhase.ANALYSIS_REVIEW: ("AG-01", "AG-03", "AG-07", "AG-08"),
    WorkflowPhase.SHARED_REVIEW: ("AG-01", "AG-04", "AG-05", "AG-06", "AG-08", "AG-09", "AG-10"),
    WorkflowPhase.SPECIALIST_VALIDATION: ("AG-01", "AG-06", "AG-07", "AG-08", "AG-10"),
    WorkflowPhase.SERVICE_CONFIRMATION: ("AG-01", "AG-06", "AG-07", "AG-08", "AG-09", "AG-10"),
    WorkflowPhase.COMPLETE: ("AG-01", "AG-06", "AG-08", "AG-10"),
}


@dataclass(frozen=True)
class OrchestratorEngine:
    """AG-01 deterministic workflow projector.

    The orchestrator derives phase/readiness from canonical SalonSessionState.
    It does not own a second workflow truth and cannot mutate canonical state.
    """

    def derive_phase(self, state: SalonSessionState) -> WorkflowPhase:
        if state.request is None:
            return WorkflowPhase.SPECIALIST_SETUP
        if state.participant_context is None or not state.input_assets:
            return WorkflowPhase.CLIENT_GUIDED_INPUT
        if state.analysis is None or not state.analysis.reviewed_by_specialist:
            return WorkflowPhase.ANALYSIS_REVIEW
        if state.recommendations is None or state.client_selection is None:
            return WorkflowPhase.SHARED_REVIEW
        validation = state.specialist_validation
        if validation is None or validation.status in {
            SpecialistValidationStatus.NOT_REVIEWED,
            SpecialistValidationStatus.REQUIRES_CHECK,
        }:
            return WorkflowPhase.SPECIALIST_VALIDATION
        if state.service_decision is None:
            return WorkflowPhase.SERVICE_CONFIRMATION
        if state.service_decision.status in {
            ServiceDecisionStatus.CHECK_FIRST,
            ServiceDecisionStatus.UNRESOLVED,
        }:
            return WorkflowPhase.SERVICE_CONFIRMATION
        return WorkflowPhase.COMPLETE

    def blockers(self, state: SalonSessionState) -> tuple[str, ...]:
        blockers: list[str] = []
        unresolved_high = [
            flag for flag in state.safety_flags
            if not flag.resolved and flag.tier in {SafetyTier.S2, SafetyTier.S3}
        ]
        if unresolved_high:
            blockers.append("UNRESOLVED_S2_S3_SAFETY")
        if state.analysis is not None and not state.analysis.reviewed_by_specialist:
            blockers.append("SPECIALIST_ANALYSIS_REVIEW_REQUIRED")
        if state.client_selection is not None:
            validation = state.specialist_validation
            if validation is None or validation.status is SpecialistValidationStatus.NOT_REVIEWED:
                blockers.append("SPECIALIST_VALIDATION_REQUIRED")
        return tuple(blockers)

    def next_actions(self, state: SalonSessionState) -> tuple[str, ...]:
        phase = self.derive_phase(state)
        actions: dict[WorkflowPhase, tuple[str, ...]] = {
            WorkflowPhase.SPECIALIST_SETUP: ("CAPTURE_REQUEST",),
            WorkflowPhase.CLIENT_GUIDED_INPUT: ("CAPTURE_PARTICIPANT_CONTEXT", "ADD_INPUT_ASSET"),
            WorkflowPhase.ANALYSIS_REVIEW: ("RUN_ANALYSIS", "SPECIALIST_REVIEW_ANALYSIS"),
            WorkflowPhase.SHARED_REVIEW: ("PUBLISH_RECOMMENDATIONS", "OPTIONAL_PREVIEW", "CLIENT_SELECTION"),
            WorkflowPhase.SPECIALIST_VALIDATION: ("SPECIALIST_VALIDATE_SELECTION", "RESOLVE_PROFESSIONAL_CHECKS"),
            WorkflowPhase.SERVICE_CONFIRMATION: ("SET_SERVICE_DECISION", "RESOLVE_PROFESSIONAL_CHECKS"),
            WorkflowPhase.COMPLETE: ("COMPILE_OUTPUTS",),
        }
        return actions[phase]

    def snapshot(self, state: SalonSessionState) -> WorkflowSnapshot:
        phase = self.derive_phase(state)
        return WorkflowSnapshot(
            tenant_id=state.tenant_id,
            session_id=state.session_id,
            revision=state.revision,
            phase=phase,
            allowed_agent_ids=_PHASE_AGENTS[phase],
            next_actions=self.next_actions(state),
            blockers=self.blockers(state),
            terminal=phase is WorkflowPhase.COMPLETE,
        )

    def require_agent_allowed(self, state: SalonSessionState, agent_id: str) -> None:
        snapshot = self.snapshot(state)
        if agent_id not in snapshot.allowed_agent_ids:
            raise OrchestrationRejected(
                f"{agent_id} is not allowed in workflow phase {snapshot.phase}"
            )
