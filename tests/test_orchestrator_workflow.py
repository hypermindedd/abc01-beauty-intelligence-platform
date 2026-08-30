from abc_core.orchestration import OrchestratorEngine, OrchestrationRejected, WorkflowPhase
from abc_core.state.enums import ActorType, RecommendationRole, SafetyTier, ServiceDecisionStatus, SpecialistValidationStatus
from abc_core.state.models import (
    ActorContext,
    AnalysisState,
    ClientSelection,
    InputAsset,
    ParticipantContext,
    RecommendationOption,
    RecommendationSet,
    RequestState,
    SafetyFlag,
    SalonSessionState,
    ServiceDecision,
    SpecialistValidation,
)
from abc_core.state.mutation import SessionMutationEngine


TENANT = "tenant-1"
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="specialist-1", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="client-1", tenant_id=TENANT)
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="system", tenant_id=TENANT)


def base_state():
    return SalonSessionState(tenant_id=TENANT, session_id="session-1")


def state_through_recommendations():
    m = SessionMutationEngine()
    s = base_state()
    s = m.set_request(s, SPECIALIST, RequestState(request_id="req-1", service_ids=("SVC-01-001",)))
    s = m.set_participant_context(s, CLIENT, ParticipantContext(context_id="ctx-1"))
    s = m.add_input_asset(s, CLIENT, InputAsset(asset_id="asset-1", media_type="image/jpeg"))
    s = m.set_analysis(s, SPECIALIST, AnalysisState(analysis_id="analysis-1", summary="reviewed", reviewed_by_specialist=True))
    recs = RecommendationSet(
        recommendation_set_id="rec-1",
        core_options=(
            RecommendationOption(option_id="opt-a", title="A", role=RecommendationRole.BEST_FIT),
            RecommendationOption(option_id="opt-b", title="B", role=RecommendationRole.ALTERNATIVE),
            RecommendationOption(option_id="opt-c", title="C", role=RecommendationRole.BOLDER),
        ),
    )
    return m.publish_recommendations(s, SYSTEM, recs)


def test_phase_is_derived_from_canonical_state_only():
    o = OrchestratorEngine()
    m = SessionMutationEngine()
    s = base_state()
    assert o.snapshot(s).phase is WorkflowPhase.SPECIALIST_SETUP

    s = m.set_request(s, SPECIALIST, RequestState(request_id="req-1"))
    assert o.snapshot(s).phase is WorkflowPhase.CLIENT_GUIDED_INPUT

    s = m.set_participant_context(s, CLIENT, ParticipantContext(context_id="ctx-1"))
    s = m.add_input_asset(s, CLIENT, InputAsset(asset_id="asset-1", media_type="image/jpeg"))
    assert o.snapshot(s).phase is WorkflowPhase.ANALYSIS_REVIEW

    s = m.set_analysis(s, SPECIALIST, AnalysisState(analysis_id="analysis-1", reviewed_by_specialist=True))
    assert o.snapshot(s).phase is WorkflowPhase.SHARED_REVIEW


def test_selection_requires_specialist_validation_phase():
    o = OrchestratorEngine()
    m = SessionMutationEngine()
    s = state_through_recommendations()
    s = m.select_option(s, CLIENT, ClientSelection(selection_id="sel-1", option_id="opt-a"))
    snapshot = o.snapshot(s)
    assert snapshot.phase is WorkflowPhase.SPECIALIST_VALIDATION
    assert "SPECIALIST_VALIDATION_REQUIRED" in snapshot.blockers
    assert "AG-07" in snapshot.allowed_agent_ids


def test_passed_validation_advances_to_service_confirmation():
    o = OrchestratorEngine()
    m = SessionMutationEngine()
    s = state_through_recommendations()
    s = m.select_option(s, CLIENT, ClientSelection(selection_id="sel-1", option_id="opt-a"))
    s = m.set_specialist_validation(
        s,
        SPECIALIST,
        SpecialistValidation(validation_id="val-1", status=SpecialistValidationStatus.PASSED),
    )
    assert o.snapshot(s).phase is WorkflowPhase.SERVICE_CONFIRMATION


def test_proceed_becomes_complete_but_check_first_remains_confirmation():
    o = OrchestratorEngine()
    m = SessionMutationEngine()
    s = state_through_recommendations()
    s = m.select_option(s, CLIENT, ClientSelection(selection_id="sel-1", option_id="opt-a"))
    s = m.set_specialist_validation(
        s,
        SPECIALIST,
        SpecialistValidation(validation_id="val-1", status=SpecialistValidationStatus.PASSED),
    )
    check = m.set_service_decision(
        s,
        SPECIALIST,
        ServiceDecision(decision_id="decision-1", status=ServiceDecisionStatus.CHECK_FIRST),
    )
    assert o.snapshot(check).phase is WorkflowPhase.SERVICE_CONFIRMATION

    proceed = m.set_service_decision(
        s,
        SPECIALIST,
        ServiceDecision(decision_id="decision-2", status=ServiceDecisionStatus.PROCEED),
    )
    assert o.snapshot(proceed).phase is WorkflowPhase.COMPLETE
    assert o.snapshot(proceed).terminal is True


def test_unresolved_high_safety_is_explicit_orchestration_blocker():
    o = OrchestratorEngine()
    m = SessionMutationEngine()
    s = state_through_recommendations()
    s = m.select_option(s, CLIENT, ClientSelection(selection_id="sel-1", option_id="opt-a"))
    s = m.add_safety_flag(
        s,
        SYSTEM,
        SafetyFlag(flag_id="flag-1", tier=SafetyTier.S2, reason="professional check required"),
    )
    snapshot = o.snapshot(s)
    assert "UNRESOLVED_S2_S3_SAFETY" in snapshot.blockers
    assert "AG-08" in snapshot.allowed_agent_ids


def test_orchestrator_does_not_mutate_canonical_state():
    o = OrchestratorEngine()
    s = base_state()
    before = s.canonical_snapshot()
    _ = o.snapshot(s)
    assert s.canonical_snapshot() == before
    assert s.revision == 0


def test_agent_routing_fails_closed_outside_phase_allowlist():
    o = OrchestratorEngine()
    s = base_state()
    try:
        o.require_agent_allowed(s, "AG-09")
    except OrchestrationRejected:
        pass
    else:
        raise AssertionError("AG-09 must not dispatch during SPECIALIST_SETUP")
