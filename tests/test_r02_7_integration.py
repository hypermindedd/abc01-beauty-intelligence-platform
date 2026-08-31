from __future__ import annotations

import pytest

from abc_core.output import OutputAudience, OutputRequest
from abc_core.r02_7_runtime import R027ServiceSafetyOutputRuntime
from abc_core.service_intelligence import ServiceResolutionError
from abc_core.state import ActorContext, ActorType, AnalysisState, SafetyFlag, SafetyTier, SalonSessionState, SessionMutationEngine
from abc_core.tenancy import SalonConfig


TENANT = "T1"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-08", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP1", tenant_id=TENANT)


def config(*ids: str) -> SalonConfig:
    return SalonConfig(tenant_id=TENANT, salon_id="SALON1", display_name="Salon", enabled_service_ids=ids)


def test_r02_7_runtime_integrates_service_safety_and_output_from_one_truth_state():
    mutation = SessionMutationEngine()
    state = SalonSessionState(tenant_id=TENANT, session_id="S1")
    state = mutation.set_analysis(
        state, SPECIALIST,
        AnalysisState(analysis_id="A1", shared_summary="shared", specialist_summary="technical", strategy_summary="strategy", reviewed_by_specialist=True),
    )
    state = mutation.add_safety_flag(state, SYSTEM, SafetyFlag(flag_id="F1", tier=SafetyTier.S2, reason="professional check"))
    before = state.canonical_snapshot()
    context = R027ServiceSafetyOutputRuntime().compile(
        state=state,
        salon_config=config("CTRL-006", "SVC-01-007"),
        service_ids=("CTRL-006",),
        output_request=OutputRequest(("OUT-01", "OUT-17"), OutputAudience.SHARED),
    )
    assert context.services[0].definition.knowledge_owners == ("ABC-KB-013",)
    assert context.safety.highest_tier is SafetyTier.S2
    assert context.safety.professional_check_required is True
    assert context.output["analysis"]["shared_summary"] == "shared"
    assert "session_id" not in context.output
    assert state.canonical_snapshot() == before


def test_r02_7_runtime_blocks_disabled_service_before_output_projection():
    with pytest.raises(ServiceResolutionError, match="not enabled"):
        R027ServiceSafetyOutputRuntime().compile(
            state=SalonSessionState(tenant_id=TENANT, session_id="S1"),
            salon_config=config(),
            service_ids=("SVC-01-001",),
            output_request=OutputRequest(("OUT-01",), OutputAudience.SHARED),
        )


def test_r02_7_complete_look_never_hides_unavailable_component():
    with pytest.raises(ServiceResolutionError, match="component"):
        R027ServiceSafetyOutputRuntime().compile(
            state=SalonSessionState(tenant_id=TENANT, session_id="S1"),
            salon_config=config("CTRL-009", "SVC-01-006", "SVC-03-005"),
            service_ids=("CTRL-009",),
            output_request=OutputRequest(("OUT-01",), OutputAudience.SPECIALIST),
        )
