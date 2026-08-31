from __future__ import annotations

import pytest

from abc_core.integration_bindings import R02_7_AGENT_BINDINGS
from abc_core.output import OUTPUT_REGISTRY, OutputAudience, OutputCompiler, OutputContractViolation, OutputRequest
from abc_core.safety import SafetyEngine
from abc_core.service_intelligence import FORBIDDEN_SERVICE_IDS, SERVICE_REGISTRY, ServiceIntelligenceEngine, ServiceResolutionError
from abc_core.state import (
    ActorContext, ActorType, AnalysisState, SafetyFlag, SafetyTier, SalonSessionState,
    ServiceDecisionStatus, SessionMutationEngine,
)
from abc_core.tenancy import SalonConfig


TENANT = "T1"
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP1", tenant_id=TENANT)
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-08", tenant_id=TENANT)


def config(*ids: str) -> SalonConfig:
    return SalonConfig(tenant_id=TENANT, salon_id="SALON1", display_name="Salon", enabled_service_ids=ids)


def test_r02_7_agent_bindings_are_exact():
    assert R02_7_AGENT_BINDINGS == {
        "AG-06": "SERVICE_INTELLIGENCE",
        "AG-08": "SAFETY_AND_BOUNDARY_CONTROL",
        "AG-10": "OUTPUT_AND_HANDOFF",
    }


def test_service_registry_covers_exact_active_ontology_and_excludes_forbidden():
    assert len([x for x in SERVICE_REGISTRY if x.startswith("SVC-01-")]) == 7
    assert len([x for x in SERVICE_REGISTRY if x.startswith("SVC-02-")]) == 9
    assert len([x for x in SERVICE_REGISTRY if x.startswith("SVC-03-")]) == 7
    assert len([x for x in SERVICE_REGISTRY if x.startswith("SVC-04-")]) == 7
    assert len([x for x in SERVICE_REGISTRY if x.startswith("SVC-05-")]) == 9
    assert {f"CTRL-{i:03d}" for i in range(1, 11)} <= set(SERVICE_REGISTRY)
    assert not FORBIDDEN_SERVICE_IDS & set(SERVICE_REGISTRY)


def test_unknown_and_forbidden_service_ids_fail_closed_without_prefix_guessing():
    engine = ServiceIntelligenceEngine()
    with pytest.raises(ServiceResolutionError, match="unknown"):
        engine.resolve("SVC-01-999", config("SVC-01-999"))
    for service_id in FORBIDDEN_SERVICE_IDS:
        with pytest.raises(ServiceResolutionError, match="forbidden"):
            engine.resolve(service_id, config(service_id))


def test_controlled_complete_look_preserves_component_capability_and_fails_closed():
    engine = ServiceIntelligenceEngine()
    partial = engine.resolve("CTRL-009", config("CTRL-009", "SVC-01-006", "SVC-03-005"))
    assert partial.definition.coordination_only is True
    assert partial.unresolved_component_ids == ("SVC-04-007",)
    with pytest.raises(ServiceResolutionError, match="component"):
        engine.require_executable_capability(partial)
    complete = engine.resolve("CTRL-009", config("CTRL-009", "SVC-01-006", "SVC-03-005", "SVC-04-007"))
    engine.require_executable_capability(complete)


def test_safety_propagates_service_baseline_and_unresolved_high_flags():
    service = ServiceIntelligenceEngine().resolve("CTRL-006", config("CTRL-006", "SVC-01-007"))
    assessment = SafetyEngine().assess(SalonSessionState(tenant_id=TENANT, session_id="S1"), (service,))
    assert assessment.highest_tier is SafetyTier.S2
    assert assessment.professional_check_required is True
    assert ServiceDecisionStatus.PROCEED not in assessment.permitted_decisions

    state = SessionMutationEngine().add_safety_flag(
        SalonSessionState(tenant_id=TENANT, session_id="S1"), SYSTEM,
        SafetyFlag(flag_id="F1", tier=SafetyTier.S3, reason="stop condition"),
    )
    assessment = SafetyEngine().assess(state, ())
    assert assessment.highest_tier is SafetyTier.S3
    assert assessment.permitted_decisions == (ServiceDecisionStatus.STOP, ServiceDecisionStatus.DEFER, ServiceDecisionStatus.UNRESOLVED)


def test_provider_never_resolves_professional_safety_flag():
    flag = SafetyFlag(flag_id="F1", tier=SafetyTier.S2, reason="professional check")
    assert SafetyEngine().provider_may_resolve_flag(flag) is False


def test_output_registry_is_exact_out_01_through_out_17_without_invented_labels():
    assert tuple(OUTPUT_REGISTRY) == tuple(f"OUT-{i:02d}" for i in range(1, 18))
    assert all(row["authority_label"] is None for row in OUTPUT_REGISTRY.values())


def test_output_compilation_is_read_only_and_shared_projection_hides_raw_runtime_ids():
    mutation = SessionMutationEngine()
    state = SalonSessionState(tenant_id=TENANT, session_id="S1")
    state = mutation.set_analysis(
        state, SPECIALIST,
        AnalysisState(
            analysis_id="A1", shared_summary="client-safe", specialist_summary="technical detail",
            strategy_summary="strategy", reviewed_by_specialist=True,
        ),
    )
    before = state.model_dump(mode="json")
    compiler = OutputCompiler()
    shared = compiler.compile(state, OutputRequest(("OUT-01",), OutputAudience.SHARED))
    specialist = compiler.compile(state, OutputRequest(("OUT-01",), OutputAudience.SPECIALIST))
    assert shared["analysis"]["shared_summary"] == "client-safe"
    assert "analysis_id" not in shared["analysis"]
    assert "session_id" not in shared
    assert "output_ids" not in shared
    assert "specialist_summary" not in shared["analysis"]
    assert specialist["analysis"]["analysis_id"] == "A1"
    assert specialist["analysis"]["specialist_summary"] == "technical detail"
    assert state.model_dump(mode="json") == before


def test_output_does_not_invent_booking_or_payment_and_rejects_unknown_output():
    compiler = OutputCompiler()
    state = SalonSessionState(tenant_id=TENANT, session_id="S1")
    payload = compiler.compile(state, OutputRequest(("OUT-17",), OutputAudience.SHARED))
    assert payload["execution_claims"] == {"booking_completed": False, "payment_completed": False}
    with pytest.raises(OutputContractViolation):
        compiler.compile(state, OutputRequest(("OUT-99",), OutputAudience.SHARED))
