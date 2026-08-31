from __future__ import annotations

from dataclasses import dataclass

from abc_core.state import SafetyTier


class ServiceResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceDefinition:
    service_id: str
    family: str
    knowledge_owners: tuple[str, ...]
    baseline_safety: SafetyTier
    controlled: bool = False
    component_service_ids: tuple[str, ...] = ()
    coordination_only: bool = False


@dataclass(frozen=True)
class ServiceResolution:
    requested_id: str
    definition: ServiceDefinition
    salon_enabled: bool
    unresolved_component_ids: tuple[str, ...] = ()
