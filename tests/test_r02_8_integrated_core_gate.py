from __future__ import annotations

import pytest

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
from abc_core.r02_8_gate import IntegratedCoreGate, IntegratedCoreGateViolation
from abc_core.recommendation import (
    CandidateDirection,
    ChangeIntensity,
    DirectionComponent,
    RecommendationEngine,
    compile_recommendation_set,
)
from abc_core.state import (
    ActorContext,
    ActorType,
    ClientSelection,
    EvidenceClass,
    InputAsset,
    PreviewRevision,
    PreviewStatus,
    RequestState,
    SalonSessionState,
    ServiceDecision,
    ServiceDecisionStatus,
    SessionMutationEngine,
    SpecialistValidation,
    SpecialistValidationStatus,
)
from abc_core.tenancy import SalonConfig


TENANT = "T-R028"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-04", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-8", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-8", tenant_id=TENANT)
VISUAL = ActorContext(actor_type=ActorType.VISUAL_RUNTIME, actor_id="VR-8", tenant_id=TENANT)


CASES = (
    (Domain.HAIR, "SVC-01-001", ("SVC-01-001",), False),
    (Domain.HAIR_COLOR, "SVC-02-001", ("SVC-02-001",), False),
    (Domain.MAKEUP, "SVC-03-001", ("SVC-03-001",), False),
    (Domain.NAILS, "SVC-04-001", ("SVC-04-001",), False),
    (Domain.MENS_HAIR_BEARD, "SVC-05-001", ("SVC-05-001",), False),
    (
        Domain.BRIDAL_GROOM,
        "CTRL-009",
        ("CTRL-009", "SVC-01-006", "SVC-03-005", "SVC-04-007"),
        False,
    ),
    (Domain.CONTROLLED_SERVICE, "CTRL-007", ("CTRL-007",), True),
)


def _build_state(domain: Domain, service_id: str, *, proceed: bool) -> SalonSessionState:
    plan = CAPTURE_PLANS[domain]
    capture_inputs = tuple(
        CaptureInput(asset_id=f"{domain.value}-A{i}", view=req.view, quality=ImageQuality.USABLE)
        for i, req in enumerate(plan.requirements)
    )
    analysis_engine = CrossDomainAnalysisEngine()
    assessment = analysis_engine.assess_capture(plan, capture_inputs)
    finding = AnalysisFinding(
        finding_id=f"F-{domain.value}",
        domain=domain,
        statement=f"observable {domain.value} source state",
        evidence_class=EvidenceClass.OBSERVED,
        source_asset_ids=(capture_inputs[0].asset_id,),
    )
    bundle = BeautyAnalysisBundle(
        analysis_id=f"AN-{domain.value}",
        capture_assessment=assessment,
        findings=(finding,),
        shared_summary=f"shared {domain.value} analysis",
        specialist_summary=f"specialist {domain.value} analysis",
        strategy=AnalysisStrategy(
            strategy_id=f"STR-{domain.value}",
            summary="preserve source reality and construct a service-valid direction",
        ),
    )
    reviewed = analysis_engine.mark_specialist_reviewed(bundle, specialist_actor_id=SPECIALIST.actor_id)

    mutation = SessionMutationEngine()
    state = SalonSessionState(tenant_id=TENANT, session_id=f"S-{domain.value}")
    state = mutation.set_request(
        state,
        SYSTEM,
        RequestState(request_id=f"REQ-{domain.value}", service_ids=(service_id,)),
    )
    for capture in capture_inputs:
        state = mutation.add_input_asset(
            state,
            SPECIALIST,
            InputAsset(asset_id=capture.asset_id, media_type="image/test"),
        )
    for evidence in compile_evidence_items(reviewed):
        state = mutation.add_evidence(state, SYSTEM, evidence)
    state = mutation.set_analysis(state, SPECIALIST, compile_analysis_state(reviewed))

    candidate = CandidateDirection(
        option_id=f"OPT-{domain.value}",
        title=f"Governed {domain.value} direction",
        components=(
            DirectionComponent(
                component_id=f"COMP-{domain.value}",
                domain=domain,
                label=f"{domain.value} component",
                service_ids=(service_id,),
                rationale="evidence-grounded service-valid component",
            ),
        ),
        intensity=ChangeIntensity.MODERATE,
        maintenance="moderate",
        tradeoff="bounded visible change",
        source_constraints=("preserve source reality",),
    )
    compilation = RecommendationEngine().compile(
        analysis=reviewed,
        candidates=(candidate,),
        source_reality={},
    )
    recommendations = compile_recommendation_set(
        compilation,
        recommendation_set_id=f"REC-{domain.value}",
    )
    state = mutation.publish_recommendations(state, SYSTEM, recommendations)
    state = mutation.select_option(
        state,
        CLIENT,
        ClientSelection(selection_id=f"SEL-{domain.value}", option_id=candidate.option_id),
    )

    if proceed:
        state = mutation.set_specialist_validation(
            state,
            SPECIALIST,
            SpecialistValidation(
                validation_id=f"VAL-{domain.value}",
                status=SpecialistValidationStatus.PASSED,
            ),
        )
        state = mutation.set_service_decision(
            state,
            SPECIALIST,
            ServiceDecision(decision_id=f"DEC-{domain.value}", status=ServiceDecisionStatus.PROCEED),
        )
    return state


def _config(*enabled: str) -> SalonConfig:
    return SalonConfig(
        tenant_id=TENANT,
        salon_id="SALON-R028",
        display_name="R02.8 Test Salon",
        enabled_service_ids=enabled,
    )


@pytest.mark.parametrize("domain,service_id,enabled,professional_check", CASES)
def test_r02_8_full_cross_domain_core_matrix_passes_with_unavailable_capability_honesty(
    domain: Domain,
    service_id: str,
    enabled: tuple[str, ...],
    professional_check: bool,
):
    state = _build_state(domain, service_id, proceed=not professional_check)
    before = state.canonical_snapshot()
    report = IntegratedCoreGate().evaluate(
        state=state,
        salon_config=_config(*enabled),
        domain=domain,
        service_ids=(service_id,),
    )

    assert report.passed is True
    assert report.context.safety.professional_check_required is professional_check
    assert report.context.output["safety_attention_required"] is professional_check
    assert "session_id" not in report.context.output
    assert "output_ids" not in report.context.output
    assert state.canonical_snapshot() == before
    assert set(report.unavailable_capabilities) == {
        "production_auth",
        "production_persistence",
        "external_visual_provider",
        "deterministic_full_frame_lock_compositor",
        "live_cross_domain_validation",
        "pilot_ready",
        "production_ready",
    }


def test_r02_8_ctrl009_fails_closed_when_any_required_component_is_unavailable():
    state = _build_state(Domain.BRIDAL_GROOM, "CTRL-009", proceed=True)
    with pytest.raises(Exception, match="component"):
        IntegratedCoreGate().evaluate(
            state=state,
            salon_config=_config("CTRL-009", "SVC-01-006", "SVC-03-005"),
            domain=Domain.BRIDAL_GROOM,
            service_ids=("CTRL-009",),
        )


def test_r02_8_unknown_service_never_inherits_semantics_from_prefix():
    state = _build_state(Domain.HAIR, "SVC-01-001", proceed=True)
    with pytest.raises(Exception, match="unknown|not governed|forbidden"):
        IntegratedCoreGate().evaluate(
            state=state,
            salon_config=_config("SVC-01-999"),
            domain=Domain.HAIR,
            service_ids=("SVC-01-999",),
        )


def test_r02_8_rejects_service_decision_that_bypasses_baseline_s2_safety():
    state = _build_state(Domain.CONTROLLED_SERVICE, "CTRL-007", proceed=False)
    mutation = SessionMutationEngine()
    state = mutation.set_specialist_validation(
        state,
        SPECIALIST,
        SpecialistValidation(validation_id="VAL-S2", status=SpecialistValidationStatus.PASSED),
    )
    # The canonical mutation layer does not itself own service-registry baseline safety.
    # R02.8 must therefore fail closed when the integrated AG-06/08 view contradicts
    # an otherwise structurally valid PROCEED decision.
    state = mutation.set_service_decision(
        state,
        SPECIALIST,
        ServiceDecision(decision_id="DEC-S2", status=ServiceDecisionStatus.PROCEED),
    )
    with pytest.raises(RuntimeError, match="contradicts integrated safety"):
        IntegratedCoreGate().evaluate(
            state=state,
            salon_config=_config("CTRL-007"),
            domain=Domain.CONTROLLED_SERVICE,
            service_ids=("CTRL-007",),
        )


def test_r02_8_rejects_qa_approved_preview_when_visual_runtime_capabilities_are_unavailable():
    state = _build_state(Domain.HAIR, "SVC-01-001", proceed=True)
    state = SessionMutationEngine().record_preview_revision(
        state,
        VISUAL,
        PreviewRevision(
            revision_id="PV-1",
            source_asset_id=state.input_assets[0].asset_id,
            option_id=state.client_selection.option_id,
            status=PreviewStatus.QA_APPROVED,
            qa_approved=True,
        ),
    )
    with pytest.raises(IntegratedCoreGateViolation, match="visual capabilities are unavailable"):
        IntegratedCoreGate().evaluate(
            state=state,
            salon_config=_config("SVC-01-001"),
            domain=Domain.HAIR,
            service_ids=("SVC-01-001",),
        )


def test_r02_8_rejects_wrong_capture_domain_even_when_other_state_is_valid():
    state = _build_state(Domain.HAIR, "SVC-01-001", proceed=True)
    with pytest.raises(IntegratedCoreGateViolation, match="capture plan"):
        IntegratedCoreGate().evaluate(
            state=state,
            salon_config=_config("SVC-01-001"),
            domain=Domain.MAKEUP,
            service_ids=("SVC-01-001",),
        )
