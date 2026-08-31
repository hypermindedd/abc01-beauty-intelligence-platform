from abc_core.analysis import (
    AnalysisFinding,
    AnalysisStrategy,
    BeautyAnalysisBundle,
    CAPTURE_PLANS,
    CaptureInput,
    CrossDomainAnalysisEngine,
    Domain,
    ImageQuality,
    compile_analysis_state,
    compile_evidence_items,
)
from abc_core.state.enums import EvidenceClass


def test_validated_bundle_compiles_to_one_canonical_analysis_state():
    engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.HAIR]
    inputs = tuple(
        CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.USABLE)
        for i, req in enumerate(plan.requirements)
    )
    assessment = engine.assess_capture(plan, inputs)
    finding = AnalysisFinding(
        finding_id="F1",
        domain=Domain.HAIR,
        statement="visible hair finding",
        evidence_class=EvidenceClass.OBSERVED,
        source_asset_ids=("A0",),
    )
    bundle = BeautyAnalysisBundle(
        analysis_id="AN-1",
        capture_assessment=assessment,
        findings=(finding,),
        shared_summary="shared",
        specialist_summary="technical",
        strategy=AnalysisStrategy(strategy_id="STR-1", summary="strategy"),
    )

    state = compile_analysis_state(bundle)
    evidence = compile_evidence_items(bundle)

    assert state.analysis_id == "AN-1"
    assert state.capture_sufficient is True
    assert state.capture_plan_ids == ("CAP-HAIR-v1",)
    assert state.finding_ids == ("F1",)
    assert state.shared_summary == "shared"
    assert state.specialist_summary == "technical"
    assert state.strategy_summary == "strategy"
    assert evidence[0].evidence_class is EvidenceClass.OBSERVED
    assert evidence[0].statement == "visible hair finding"
