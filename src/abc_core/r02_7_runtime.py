from __future__ import annotations

from dataclasses import dataclass

from abc_core.output import OutputAudience, OutputCompiler, OutputRequest
from abc_core.safety import SafetyAssessment, SafetyEngine
from abc_core.service_intelligence import ServiceIntelligenceEngine, ServiceResolution
from abc_core.state import SalonSessionState
from abc_core.tenancy import SalonConfig


@dataclass(frozen=True)
class ServiceSafetyOutputContext:
    services: tuple[ServiceResolution, ...]
    safety: SafetyAssessment
    output: dict


class R027ServiceSafetyOutputRuntime:
    """Governed integration boundary for AG-06 → AG-08 → AG-10.

    Service capability is resolved before safety. Safety is computed from the same
    canonical state that the output compiler projects. None of these layers may
    mutate the canonical session state.
    """

    def __init__(self) -> None:
        self.services = ServiceIntelligenceEngine()
        self.safety = SafetyEngine()
        self.outputs = OutputCompiler()

    def compile(
        self,
        *,
        state: SalonSessionState,
        salon_config: SalonConfig,
        service_ids: tuple[str, ...],
        output_request: OutputRequest,
        require_executable_capability: bool = True,
    ) -> ServiceSafetyOutputContext:
        before = state.canonical_snapshot()
        resolutions = tuple(self.services.resolve(service_id, salon_config) for service_id in service_ids)
        if require_executable_capability:
            for resolution in resolutions:
                self.services.require_executable_capability(resolution)
        safety = self.safety.assess(state, resolutions)
        if state.service_decision is not None and state.service_decision.status not in safety.permitted_decisions:
            raise RuntimeError("canonical service decision contradicts integrated safety assessment")
        output = self.outputs.compile(state, output_request)
        if output_request.audience is OutputAudience.SHARED:
            # Shared safety attention must include service-baseline safety, not only
            # session flags already present in canonical state.
            output = dict(output)
            output["safety_attention_required"] = safety.professional_check_required
        if state.canonical_snapshot() != before:
            raise RuntimeError("R02.7 read-only integration mutated canonical truth state")
        return ServiceSafetyOutputContext(resolutions, safety, output)
