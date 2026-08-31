from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from abc_core.analysis import CAPTURE_PLANS, Domain
from abc_core.capabilities import CAPABILITIES, CapabilityState
from abc_core.output import OutputAudience, OutputRequest
from abc_core.r02_7_runtime import R027ServiceSafetyOutputRuntime, ServiceSafetyOutputContext
from abc_core.state import PreviewStatus, SalonSessionState, ServiceDecisionStatus, SpecialistValidationStatus
from abc_core.tenancy import SalonConfig


class IntegratedCoreGateViolation(RuntimeError):
    pass


class GateCheckStatus(StrEnum):
    PASS = "PASS"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GateCheck:
    check_id: str
    status: GateCheckStatus
    note: str


@dataclass(frozen=True)
class IntegratedCoreGateReport:
    domain: Domain
    service_ids: tuple[str, ...]
    context: ServiceSafetyOutputContext
    checks: tuple[GateCheck, ...]
    unavailable_capabilities: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(check.status in {GateCheckStatus.PASS, GateCheckStatus.UNAVAILABLE} for check in self.checks)


@dataclass(frozen=True)
class IntegratedCoreGate:
    """R02.8 read-only integration gate over the canonical Core.

    The gate does not create a second workflow truth and does not simulate external
    infrastructure. Unavailable capabilities are reported explicitly rather than
    promoted to PASS. Any semantic inconsistency in the available Core fails closed.
    """

    capabilities: CapabilityState = CAPABILITIES

    def evaluate(
        self,
        *,
        state: SalonSessionState,
        salon_config: SalonConfig,
        domain: Domain,
        service_ids: tuple[str, ...],
        output_ids: tuple[str, ...] = ("OUT-01", "OUT-17"),
    ) -> IntegratedCoreGateReport:
        before = state.canonical_snapshot()
        checks: list[GateCheck] = []

        if state.analysis is None:
            raise IntegratedCoreGateViolation("R02.8 requires canonical analysis")
        if state.analysis.capture_sufficient is not True:
            raise IntegratedCoreGateViolation("R02.8 requires sufficient governed capture")
        expected_plan = CAPTURE_PLANS[domain].plan_id
        if expected_plan not in state.analysis.capture_plan_ids:
            raise IntegratedCoreGateViolation(
                f"analysis does not carry the governed capture plan for {domain.value}"
            )
        checks.append(GateCheck("CAPTURE_AND_ANALYSIS", GateCheckStatus.PASS, expected_plan))

        if state.recommendations is None or not state.recommendations.core_options:
            raise IntegratedCoreGateViolation("R02.8 requires at least one governed Core direction")
        if not state.analysis.reviewed_by_specialist:
            raise IntegratedCoreGateViolation("ranked recommendations require specialist-reviewed analysis")
        checks.append(GateCheck("ANALYSIS_REVIEW_GATE", GateCheckStatus.PASS, "specialist-reviewed before ranking"))

        shared_request = OutputRequest(output_ids=output_ids, audience=OutputAudience.SHARED)
        context = R027ServiceSafetyOutputRuntime().compile(
            state=state,
            salon_config=salon_config,
            service_ids=service_ids,
            output_request=shared_request,
        )
        checks.append(GateCheck("SERVICE_INTELLIGENCE", GateCheckStatus.PASS, "exact service/capability resolution"))
        checks.append(GateCheck("SAFETY_PROPAGATION", GateCheckStatus.PASS, context.safety.highest_tier.value))

        if state.service_decision is not None:
            if state.service_decision.status not in context.safety.permitted_decisions:
                raise IntegratedCoreGateViolation(
                    "canonical service decision contradicts integrated safety assessment"
                )
            if state.service_decision.status is ServiceDecisionStatus.PROCEED:
                validation = state.specialist_validation
                if validation is None or validation.status is not SpecialistValidationStatus.PASSED:
                    raise IntegratedCoreGateViolation("PROCEED requires Specialist Validation PASSED")
        checks.append(GateCheck("SERVICE_DECISION_COHERENCE", GateCheckStatus.PASS, "decision is compatible with safety"))

        forbidden_shared_keys = {"session_id", "output_ids", "safety", "client_selection", "request"}
        leaked = forbidden_shared_keys.intersection(context.output)
        if leaked:
            raise IntegratedCoreGateViolation(f"shared output leaked internal keys: {sorted(leaked)}")
        if context.output.get("execution_claims") != {"booking_completed": False, "payment_completed": False}:
            raise IntegratedCoreGateViolation("shared output contains unsupported execution claims")
        if bool(context.output.get("safety_attention_required")) != context.safety.professional_check_required:
            raise IntegratedCoreGateViolation("shared safety attention does not match integrated safety")
        checks.append(GateCheck("SHARED_OUTPUT_PRIVACY", GateCheckStatus.PASS, "client projection is reduced and safety-consistent"))

        approved_preview_exists = bool(
            state.preview
            and any(revision.status is PreviewStatus.QA_APPROVED for revision in state.preview.revisions)
        )
        if approved_preview_exists and (
            not self.capabilities.external_visual_provider
            or not self.capabilities.deterministic_full_frame_lock_compositor
        ):
            raise IntegratedCoreGateViolation(
                "QA-approved visual preview cannot be accepted while required visual capabilities are unavailable"
            )

        unavailable = tuple(
            name for name, available in self.capabilities.public().items() if not available
        )
        for capability in unavailable:
            checks.append(
                GateCheck(
                    f"CAPABILITY::{capability}",
                    GateCheckStatus.UNAVAILABLE,
                    "explicitly unavailable; no readiness claim",
                )
            )

        if state.canonical_snapshot() != before:
            raise IntegratedCoreGateViolation("R02.8 gate mutated canonical truth state")
        checks.append(GateCheck("ONE_CANONICAL_TRUTH_STATE", GateCheckStatus.PASS, "read-only gate"))

        return IntegratedCoreGateReport(
            domain=domain,
            service_ids=service_ids,
            context=context,
            checks=tuple(checks),
            unavailable_capabilities=unavailable,
        )
