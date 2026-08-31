import pytest

from abc_core.analysis import (
    AnalysisContractViolation,
    AnalysisExtractionResult,
    AnalysisFinding,
    AnalysisStrategy,
    BeautyAnalysisBundle,
    CAPTURE_PLANS,
    CaptureInput,
    CrossDomainAnalysisEngine,
    Domain,
    FindingVisibility,
    GovernedAnalysisRuntime,
    ImageQuality,
    capture_plan_for_services,
)
from abc_core.state.enums import EvidenceClass


def test_hair_capture_fails_closed_when_required_view_missing():
    engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.HAIR]
    assessment = engine.assess_capture(
        plan,
        (
            CaptureInput(asset_id="A1", view=plan.requirements[0].view, quality=ImageQuality.USABLE),
        ),
    )
    assert assessment.sufficient is False
    assert "HAIR-BACK" in assessment.missing_requirement_ids


def test_limited_image_does_not_satisfy_required_capture():
    engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.NAILS]
    assessment = engine.assess_capture(
        plan,
        tuple(
            CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.LIMITED)
            for i, req in enumerate(plan.requirements)
        ),
    )
    assert assessment.sufficient is False
    assert set(assessment.limited_requirement_ids) == {"NAILS-HANDS", "NAILS-DETAIL"}


def test_service_domain_resolution_never_guesses_unknown_service():
    mapping = {"SVC-HAIR-DEMO": Domain.HAIR}
    plans = capture_plan_for_services(("SVC-HAIR-DEMO",), service_domain_map=mapping)
    assert plans[0].plan_id == "CAP-HAIR-v1"
    with pytest.raises(KeyError):
        capture_plan_for_services(("SVC-UNKNOWN",), service_domain_map=mapping)


def test_observed_finding_requires_asset_provenance():
    with pytest.raises(ValueError):
        AnalysisFinding(
            finding_id="F1",
            domain=Domain.HAIR,
            statement="visible observation",
            evidence_class=EvidenceClass.OBSERVED,
        )


def test_unknown_finding_cannot_claim_sources():
    with pytest.raises(ValueError):
        AnalysisFinding(
            finding_id="F1",
            domain=Domain.HAIR_COLOR,
            statement="history unknown",
            evidence_class=EvidenceClass.UNKNOWN,
            source_asset_ids=("A1",),
        )


def test_inferred_finding_requires_provenance_at_engine_boundary():
    engine = CrossDomainAnalysisEngine()
    finding = AnalysisFinding(
        finding_id="F1",
        domain=Domain.HAIR,
        statement="explicitly marked inference",
        evidence_class=EvidenceClass.INFERRED,
    )
    with pytest.raises(AnalysisContractViolation):
        engine.validate_findings((finding,), known_asset_ids=set(), known_evidence_ids=set())


def test_shared_projection_hides_specialist_only_detail_without_second_truth():
    engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.MAKEUP]
    inputs = tuple(
        CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.USABLE)
        for i, req in enumerate(plan.requirements)
    )
    assessment = engine.assess_capture(plan, inputs)
    findings = (
        AnalysisFinding(
            finding_id="F-SHARED",
            domain=Domain.MAKEUP,
            statement="shared visible finding",
            evidence_class=EvidenceClass.OBSERVED,
            source_asset_ids=("A0",),
        ),
        AnalysisFinding(
            finding_id="F-SPECIALIST",
            domain=Domain.MAKEUP,
            statement="specialist technical detail",
            evidence_class=EvidenceClass.OBSERVED,
            source_asset_ids=("A1",),
            visibility=FindingVisibility.SPECIALIST_ONLY,
        ),
    )
    engine.validate_findings(findings, known_asset_ids={i.asset_id for i in inputs}, known_evidence_ids=set())
    bundle = BeautyAnalysisBundle(
        analysis_id="AN-1",
        capture_assessment=assessment,
        findings=findings,
        shared_summary="shared",
        specialist_summary="specialist",
        strategy=AnalysisStrategy(strategy_id="STR-1", summary="strategy"),
    )
    assert [item.finding_id for item in engine.shared_findings(bundle)] == ["F-SHARED"]
    assert len(engine.specialist_findings(bundle)) == 2


def test_specialist_review_requires_sufficient_capture_and_findings():
    engine = CrossDomainAnalysisEngine()
    plan = CAPTURE_PLANS[Domain.HAIR_COLOR]
    assessment = engine.assess_capture(plan, ())
    bundle = BeautyAnalysisBundle(
        analysis_id="AN-1",
        capture_assessment=assessment,
        findings=(),
        shared_summary="",
        specialist_summary="",
        strategy=AnalysisStrategy(strategy_id="STR-1", summary="pending"),
    )
    with pytest.raises(AnalysisContractViolation):
        engine.mark_specialist_reviewed(bundle, specialist_actor_id="SP-1")


class FakeExtractor:
    def __init__(self):
        self.calls = 0

    def extract(self, request):
        self.calls += 1
        return AnalysisExtractionResult(
            findings=(
                AnalysisFinding(
                    finding_id="F-LIVE",
                    domain=request.domain,
                    statement="provider-returned visible finding",
                    evidence_class=EvidenceClass.OBSERVED,
                    source_asset_ids=(request.capture_inputs[0].asset_id,),
                ),
            ),
            shared_summary="shared summary",
            specialist_summary="specialist summary",
            strategy=AnalysisStrategy(strategy_id="STR-LIVE", summary="evidence-grounded strategy"),
        )


def test_governed_runtime_blocks_provider_when_capture_is_insufficient():
    extractor = FakeExtractor()
    runtime = GovernedAnalysisRuntime(CrossDomainAnalysisEngine(), extractor)
    with pytest.raises(AnalysisContractViolation):
        runtime.run(
            tenant_id="T1",
            session_id="S1",
            domain=Domain.HAIR,
            service_ids=("SVC-DEMO",),
            plan=CAPTURE_PLANS[Domain.HAIR],
            capture_inputs=(),
        )
    assert extractor.calls == 0


def test_governed_runtime_quarantines_then_validates_provider_output():
    extractor = FakeExtractor()
    engine = CrossDomainAnalysisEngine()
    runtime = GovernedAnalysisRuntime(engine, extractor)
    plan = CAPTURE_PLANS[Domain.MENS_HAIR_BEARD]
    inputs = tuple(
        CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.STRONG)
        for i, req in enumerate(plan.requirements)
    )
    bundle = runtime.run(
        tenant_id="T1",
        session_id="S1",
        domain=Domain.MENS_HAIR_BEARD,
        service_ids=("SVC-DEMO",),
        plan=plan,
        capture_inputs=inputs,
    )
    assert extractor.calls == 1
    assert bundle.capture_assessment.sufficient is True
    assert bundle.findings[0].evidence_class is EvidenceClass.OBSERVED
    assert bundle.specialist_reviewed is False


def test_specialist_review_is_separate_from_provider_analysis():
    extractor = FakeExtractor()
    engine = CrossDomainAnalysisEngine()
    runtime = GovernedAnalysisRuntime(engine, extractor)
    plan = CAPTURE_PLANS[Domain.NAILS]
    inputs = tuple(
        CaptureInput(asset_id=f"A{i}", view=req.view, quality=ImageQuality.USABLE)
        for i, req in enumerate(plan.requirements)
    )
    bundle = runtime.run(
        tenant_id="T1",
        session_id="S1",
        domain=Domain.NAILS,
        service_ids=("SVC-DEMO",),
        plan=plan,
        capture_inputs=inputs,
    )
    assert bundle.specialist_reviewed is False
    reviewed = engine.mark_specialist_reviewed(bundle, specialist_actor_id="SP-1")
    assert reviewed.specialist_reviewed is True
    assert reviewed.specialist_reviewer_id == "SP-1"
