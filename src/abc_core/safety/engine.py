from __future__ import annotations

from dataclasses import dataclass

from abc_core.service_intelligence import ServiceResolution
from abc_core.state import SafetyFlag, SafetyTier, SalonSessionState, ServiceDecisionStatus


@dataclass(frozen=True)
class SafetyAssessment:
    highest_tier: SafetyTier
    unresolved_flag_ids: tuple[str, ...]
    professional_check_required: bool
    permitted_decisions: tuple[ServiceDecisionStatus, ...]


class SafetyEngine:
    _ORDER = {SafetyTier.S0: 0, SafetyTier.S1: 1, SafetyTier.S2: 2, SafetyTier.S3: 3}

    def assess(self, state: SalonSessionState, services: tuple[ServiceResolution, ...]) -> SafetyAssessment:
        tiers = [resolution.definition.baseline_safety for resolution in services]
        unresolved = tuple(flag for flag in state.safety_flags if not flag.resolved)
        tiers.extend(flag.tier for flag in unresolved)
        highest = max(tiers or [SafetyTier.S0], key=self._ORDER.__getitem__)
        high = tuple(flag.flag_id for flag in unresolved if flag.tier in {SafetyTier.S2, SafetyTier.S3})
        if highest is SafetyTier.S3:
            decisions = (ServiceDecisionStatus.STOP, ServiceDecisionStatus.DEFER, ServiceDecisionStatus.UNRESOLVED)
        elif high or highest is SafetyTier.S2:
            decisions = (ServiceDecisionStatus.CHECK_FIRST, ServiceDecisionStatus.MODIFY, ServiceDecisionStatus.DEFER, ServiceDecisionStatus.UNRESOLVED)
        else:
            decisions = (ServiceDecisionStatus.PROCEED, ServiceDecisionStatus.MODIFY, ServiceDecisionStatus.CHECK_FIRST, ServiceDecisionStatus.DEFER)
        return SafetyAssessment(highest, tuple(flag.flag_id for flag in unresolved), bool(high), decisions)

    def provider_may_resolve_flag(self, flag: SafetyFlag) -> bool:
        return False
