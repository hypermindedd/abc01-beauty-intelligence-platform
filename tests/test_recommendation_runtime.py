import pytest

from abc_core.analysis import AnalysisFinding, AnalysisStrategy, BeautyAnalysisBundle, CAPTURE_PLANS, CaptureInput, CrossDomainAnalysisEngine, Domain, ImageQuality
from abc_core.recommendation import CandidateDirection, ChangeIntensity, DirectionComponent, RealityRequirement, RecommendationContractViolation, RecommendationEngine
from abc_core.state.enums import EvidenceClass, RecommendationRole


def reviewed_analysis(domain: Domain):
    analysis_engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[domain]
    inputs = tuple(CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.USABLE) for i, req in enumerate(plan.requirements))
    assessment = analysis_engine.assess_capture(plan, inputs)
    bundle = BeautyAnalysisBundle(
        analysis_id="AN-1",
        capture_assessment=assessment,
        findings=(AnalysisFinding(finding_id="F1", domain=domain, statement="visible", evidence_class=EvidenceClass.OBSERVED, source_asset_ids=("A0",)),),
        shared_summary="shared",
        specialist_summary="specialist",
        strategy=AnalysisStrategy(strategy_id="STR-1", summary="strategy"),
    )
    return analysis_engine.mark_specialist_reviewed(bundle, specialist_actor_id="SP-1")


def candidate(option_id: str, component_id: str, *, requirement=None):
    requirements = () if requirement is None else (requirement,)
    return CandidateDirection(
        option_id=option_id,
        title=f"Custom {option_id}",
        components=(DirectionComponent(component_id=component_id, domain=Domain.MENS_HAIR_BEARD, label="component", service_ids=("SVC-05-001",), rationale="evidence-grounded", evidence_ids=("F1",), reality_requirements=requirements),),
        intensity=ChangeIntensity.MODERATE,
        maintenance="moderate",
        tradeoff="tradeoff",
    )


def test_recommendation_blocked_before_specialist_review():
    analysis_engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.HAIR]
    inputs = tuple(CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.USABLE) for i, req in enumerate(plan.requirements))
    bundle = BeautyAnalysisBundle(analysis_id="AN", capture_assessment=analysis_engine.assess_capture(plan, inputs), findings=(), shared_summary="s", specialist_summary="s", strategy=AnalysisStrategy(strategy_id="STR", summary="s"))
    with pytest.raises(RecommendationContractViolation):
        RecommendationEngine().compile(analysis=bundle, candidates=(), source_reality={})


def test_source_reality_invalid_candidate_is_filtered_before_ranking():
    req = RealityRequirement(key="beard_coverage", allowed_values=("FULL", "MEDIUM"))
    invalid = candidate("X", "C-X", requirement=req)
    valid = candidate("A", "C-A")
    result = RecommendationEngine().compile(analysis=reviewed_analysis(Domain.MENS_HAIR_BEARD), candidates=(invalid, valid), source_reality={"beard_coverage": "SPARSE"})
    assert [x.option_id for x in result.core] == ["A"]
    assert result.core[0].role is RecommendationRole.BEST_FIT
    assert result.rejected[0].candidate.option_id == "X"


def test_no_filler_allows_fewer_than_three_core_directions():
    result = RecommendationEngine().compile(analysis=reviewed_analysis(Domain.MENS_HAIR_BEARD), candidates=(candidate("A", "C-A"), candidate("B", "C-B")), source_reality={})
    assert [x.role for x in result.core] == [RecommendationRole.BEST_FIT, RecommendationRole.ALTERNATIVE]
    assert len(result.core) == 2


def test_structural_duplicates_do_not_fill_core_slots():
    a = candidate("A", "SAME")
    duplicate = candidate("A2", "SAME")
    b = candidate("B", "DIFFERENT")
    result = RecommendationEngine().compile(analysis=reviewed_analysis(Domain.MENS_HAIR_BEARD), candidates=(a, duplicate, b), source_reality={})
    assert [x.option_id for x in result.core] == ["A", "B"]


def test_explore_is_explicit_and_fixed_choice_never_auto_expands():
    candidates = tuple(candidate(chr(65 + i), f"C-{i}") for i in range(6))
    engine = RecommendationEngine()
    analysis = reviewed_analysis(Domain.MENS_HAIR_BEARD)
    no_explore = engine.compile(analysis=analysis, candidates=candidates, source_reality={})
    assert no_explore.explore == ()
    explore = engine.compile(analysis=analysis, candidates=candidates, source_reality={}, explicit_explore_requested=True)
    assert len(explore.explore) == 3
    fixed = engine.compile(analysis=analysis, candidates=candidates, source_reality={}, explicit_explore_requested=True, fixed_choice=True)
    assert fixed.explore == ()
