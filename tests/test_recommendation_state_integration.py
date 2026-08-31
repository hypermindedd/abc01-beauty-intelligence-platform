from __future__ import annotations

import pytest

from abc_core.analysis import AnalysisStrategy, BeautyAnalysisBundle, CaptureAssessment, Domain
from abc_core.recommendation import (
    CandidateDirection,
    ChangeIntensity,
    DirectionComponent,
    RecommendationEngine,
    RealityRequirement,
    compile_recommendation_set,
)
from abc_core.state import (
    ActorContext,
    ActorType,
    AnalysisState,
    ClientSelection,
    MutationRejected,
    RecommendationRole,
    SalonSessionState,
    SessionMutationEngine,
)


TENANT = "T-1"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-04", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-1", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-1", tenant_id=TENANT)


def reviewed_analysis() -> BeautyAnalysisBundle:
    return BeautyAnalysisBundle(
        analysis_id="AN-1",
        capture_assessment=CaptureAssessment(plan_id="CAP-HAIR-v1", sufficient=True),
        findings=(),
        shared_summary="shared",
        specialist_summary="specialist",
        strategy=AnalysisStrategy(strategy_id="STR-1", summary="preserve source reality"),
        specialist_reviewed=True,
        specialist_reviewer_id="SP-1",
    )


def component(component_id: str, *, requirement: RealityRequirement | None = None) -> DirectionComponent:
    requirements = (requirement,) if requirement else ()
    return DirectionComponent(
        component_id=component_id,
        domain=Domain.HAIR,
        label=component_id,
        service_ids=("SVC-01-001",),
        rationale="grounded component",
        reality_requirements=requirements,
    )


def candidate(option_id: str, component_id: str, intensity: ChangeIntensity = ChangeIntensity.MODERATE) -> CandidateDirection:
    return CandidateDirection(
        option_id=option_id,
        title=f"Custom {option_id}",
        components=(component(component_id),),
        intensity=intensity,
        maintenance="moderate",
        tradeoff="visible change",
        source_constraints=("preserve identity",),
    )


def canonical_reviewed_state() -> SalonSessionState:
    mutation = SessionMutationEngine()
    state = SalonSessionState(tenant_id=TENANT, session_id="S-1")
    return mutation.set_analysis(
        state,
        SPECIALIST,
        AnalysisState(analysis_id="AN-1", reviewed_by_specialist=True),
    )


def test_engine_compiler_and_canonical_state_accept_two_valid_core_without_filler():
    engine = RecommendationEngine()
    compilation = engine.compile(
        analysis=reviewed_analysis(),
        candidates=(candidate("A", "C-A"), candidate("B", "C-B")),
        source_reality={},
    )
    assert [item.role for item in compilation.core] == [RecommendationRole.BEST_FIT, RecommendationRole.ALTERNATIVE]
    assert len(compilation.core) == 2

    recommendation_set = compile_recommendation_set(compilation, recommendation_set_id="REC-1")
    state = SessionMutationEngine().publish_recommendations(canonical_reviewed_state(), SYSTEM, recommendation_set)
    assert len(state.recommendations.core_options) == 2
    assert state.recommendations.core_options[0].components[0].component_id == "C-A"
    assert "NO_FILLER" in state.recommendations.rules_applied


def test_source_reality_invalid_candidate_is_filtered_not_used_as_filler():
    requires_long = RealityRequirement(key="hair_length", allowed_values=("LONG", "VERY_LONG"))
    invalid = CandidateDirection(
        option_id="INVALID",
        title="Requires long hair",
        components=(component("C-LONG", requirement=requires_long),),
        intensity=ChangeIntensity.HIGH,
        maintenance="high",
        tradeoff="requires unavailable source state",
    )
    compilation = RecommendationEngine().compile(
        analysis=reviewed_analysis(),
        candidates=(candidate("A", "C-A"), invalid),
        source_reality={"hair_length": "SHORT"},
    )
    assert [item.option_id for item in compilation.core] == ["A"]
    assert [item.candidate.option_id for item in compilation.rejected] == ["INVALID"]


def test_structural_duplicate_does_not_fill_another_role():
    first = candidate("A", "SAME")
    duplicate = candidate("B", "SAME")
    compilation = RecommendationEngine().compile(
        analysis=reviewed_analysis(),
        candidates=(first, duplicate),
        source_reality={},
    )
    assert len(compilation.core) == 1
    assert compilation.core[0].role is RecommendationRole.BEST_FIT


def test_explore_compilation_requires_explicit_request_at_engine_and_state_boundaries():
    candidates = tuple(candidate(option_id, component_id) for option_id, component_id in (("A", "C-A"), ("B", "C-B"), ("C", "C-C"), ("D", "C-D")))
    engine = RecommendationEngine()
    implicit = engine.compile(analysis=reviewed_analysis(), candidates=candidates, source_reality={})
    assert implicit.explore == ()

    explicit = engine.compile(
        analysis=reviewed_analysis(),
        candidates=candidates,
        source_reality={},
        explicit_explore_requested=True,
    )
    assert [item.option_id for item in explicit.explore] == ["D"]
    recommendation_set = compile_recommendation_set(explicit, recommendation_set_id="REC-X")
    with pytest.raises(MutationRejected, match="explicit"):
        SessionMutationEngine().publish_recommendations(canonical_reviewed_state(), SYSTEM, recommendation_set)
    accepted = SessionMutationEngine().publish_recommendations(
        canonical_reviewed_state(), SYSTEM, recommendation_set, explicit_explore_requested=True
    )
    assert accepted.recommendations.explore_options[0].option_id == "D"


def test_client_selection_remains_distinct_from_specialist_validation_after_compilation():
    compilation = RecommendationEngine().compile(
        analysis=reviewed_analysis(),
        candidates=(candidate("A", "C-A"),),
        source_reality={},
    )
    recommendation_set = compile_recommendation_set(compilation, recommendation_set_id="REC-SEL")
    mutation = SessionMutationEngine()
    state = mutation.publish_recommendations(canonical_reviewed_state(), SYSTEM, recommendation_set)
    state = mutation.select_option(state, CLIENT, ClientSelection(selection_id="SEL-1", option_id="A"))
    assert state.client_selection.option_id == "A"
    assert state.specialist_validation is None
