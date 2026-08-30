from __future__ import annotations

import pytest

from abc_core.state import ActorContext, ActorType, AnalysisState, ClientSelection, EvidenceClass, EvidenceItem, MutationRejected, PreviewRevision, PreviewStatus, RecommendationOption, RecommendationRole, RecommendationSet, SafetyFlag, SafetyTier, SalonSessionState, ServiceDecision, ServiceDecisionStatus, SessionMutationEngine, SpecialistValidation, SpecialistValidationStatus, compile_output_projection


ENGINE = SessionMutationEngine()
TENANT = "TENANT-1"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-01", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-1", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-1", tenant_id=TENANT)
VISUAL = ActorContext(actor_type=ActorType.VISUAL_RUNTIME, actor_id="AG-05", tenant_id=TENANT)
OUTPUT = ActorContext(actor_type=ActorType.OUTPUT_COMPILER, actor_id="AG-10", tenant_id=TENANT)


def state() -> SalonSessionState:
    return SalonSessionState(tenant_id=TENANT, session_id="S-1")


def reviewed_state() -> SalonSessionState:
    s = state()
    return ENGINE.set_analysis(s, SPECIALIST, AnalysisState(analysis_id="A-1", reviewed_by_specialist=True))


def recs(explore: int = 0) -> RecommendationSet:
    core = (
        RecommendationOption(option_id="O-A", title="A", role=RecommendationRole.BEST_FIT),
        RecommendationOption(option_id="O-B", title="B", role=RecommendationRole.ALTERNATIVE),
        RecommendationOption(option_id="O-C", title="C", role=RecommendationRole.BOLDER),
    )
    extra = tuple(RecommendationOption(option_id=f"O-E{i}", title=f"E{i}", is_explore=True) for i in range(explore))
    return RecommendationSet(recommendation_set_id="R-1", core_options=core, explore_options=extra)


def test_revision_and_append_only_audit_event_increment_together():
    s0 = state()
    s1 = ENGINE.add_evidence(s0, SYSTEM, EvidenceItem(evidence_id="E-1", evidence_class=EvidenceClass.OBSERVED, statement="visible fact"))
    assert s0.revision == 0 and not s0.audit_events
    assert s1.revision == 1 and len(s1.audit_events) == 1
    assert s1.audit_events[0].from_revision == 0 and s1.audit_events[0].to_revision == 1


def test_recommendation_is_blocked_before_specialist_review():
    with pytest.raises(MutationRejected):
        ENGINE.publish_recommendations(state(), SYSTEM, recs())


def test_only_specialist_can_mark_analysis_reviewed():
    with pytest.raises(MutationRejected):
        ENGINE.set_analysis(state(), SYSTEM, AnalysisState(analysis_id="A-1", reviewed_by_specialist=True))


def test_client_or_system_cannot_set_specialist_validation_passed():
    validation = SpecialistValidation(validation_id="V-1", status=SpecialistValidationStatus.PASSED)
    for actor in (CLIENT, SYSTEM):
        with pytest.raises(MutationRejected):
            ENGINE.set_specialist_validation(state(), actor, validation)


def test_explore_is_zero_to_three_never_relabels_core_and_max_six():
    s = reviewed_state()
    accepted = ENGINE.publish_recommendations(s, SYSTEM, recs(3))
    assert accepted.recommendations.active_count == 6
    bad_extra = RecommendationOption(option_id="O-E", title="bad", role=RecommendationRole.BEST_FIT, is_explore=True)
    with pytest.raises(MutationRejected):
        ENGINE.publish_recommendations(s, SYSTEM, RecommendationSet(recommendation_set_id="R-X", core_options=recs().core_options, explore_options=(bad_extra,)))
    with pytest.raises(MutationRejected):
        ENGINE.publish_recommendations(s, SYSTEM, recs(4))


def test_tenant_mismatch_is_fail_closed_and_original_state_is_unchanged():
    s0 = state()
    foreign = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-01", tenant_id="OTHER")
    with pytest.raises(MutationRejected):
        ENGINE.add_evidence(s0, foreign, EvidenceItem(evidence_id="E-1", evidence_class=EvidenceClass.KNOWN, statement="x"))
    assert s0.revision == 0 and not s0.evidence_set.items


def test_preview_does_not_mutate_safety_or_service_decision():
    s = ENGINE.add_safety_flag(state(), SYSTEM, SafetyFlag(flag_id="SF-1", tier=SafetyTier.S2, reason="professional check"))
    before_flags = s.safety_flags
    s2 = ENGINE.record_preview_revision(s, VISUAL, PreviewRevision(revision_id="P-1", source_asset_id="I-1", option_id="O-A", status=PreviewStatus.QUARANTINED))
    assert s2.safety_flags == before_flags
    assert s2.service_decision is None


def test_check_first_cannot_become_proceed_until_safety_resolved_and_specialist_passed():
    s = ENGINE.add_safety_flag(state(), SYSTEM, SafetyFlag(flag_id="SF-1", tier=SafetyTier.S2, reason="check"))
    with pytest.raises(MutationRejected):
        ENGINE.set_service_decision(s, SPECIALIST, ServiceDecision(decision_id="D-1", status=ServiceDecisionStatus.PROCEED))
    s = ENGINE.set_specialist_validation(s, SPECIALIST, SpecialistValidation(validation_id="V-1", status=SpecialistValidationStatus.PASSED))
    with pytest.raises(MutationRejected):
        ENGINE.set_service_decision(s, SPECIALIST, ServiceDecision(decision_id="D-2", status=ServiceDecisionStatus.PROCEED))
    s = ENGINE.resolve_safety_flag(s, SPECIALIST, "SF-1", "professional check resolved")
    s = ENGINE.set_service_decision(s, SPECIALIST, ServiceDecision(decision_id="D-3", status=ServiceDecisionStatus.PROCEED))
    assert s.service_decision.status is ServiceDecisionStatus.PROCEED


def test_commercial_eligibility_cannot_reorder_core_recommendations():
    s = ENGINE.publish_recommendations(reviewed_state(), SYSTEM, recs())
    before = tuple(o.option_id for o in s.recommendations.core_options)
    s2 = ENGINE.set_commercial_eligibility(s, SYSTEM, ("VIP", "EVENT"))
    assert tuple(o.option_id for o in s2.recommendations.core_options) == before


def test_output_projection_is_read_only_and_does_not_increment_truth_revision():
    s = reviewed_state()
    before = s.model_dump()
    projection = compile_output_projection(s, OUTPUT, ("OUT-02", "OUT-09"))
    assert projection["read_only_projection"] is True
    assert s.model_dump() == before


def test_client_selection_does_not_imply_specialist_validation():
    s = ENGINE.publish_recommendations(reviewed_state(), SYSTEM, recs())
    s = ENGINE.select_option(s, CLIENT, ClientSelection(selection_id="SEL-1", option_id="O-A"))
    assert s.client_selection.option_id == "O-A"
    assert s.specialist_validation is None
