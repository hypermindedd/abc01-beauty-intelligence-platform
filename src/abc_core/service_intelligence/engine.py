from __future__ import annotations

from abc_core.tenancy import SalonConfig
from .contracts import ServiceResolution, ServiceResolutionError
from .registry import FORBIDDEN_SERVICE_IDS, SERVICE_REGISTRY


class ServiceIntelligenceEngine:
    def resolve(self, service_id: str, salon_config: SalonConfig) -> ServiceResolution:
        if service_id in FORBIDDEN_SERVICE_IDS:
            raise ServiceResolutionError(f"forbidden/inactive service id: {service_id}")
        definition = SERVICE_REGISTRY.get(service_id)
        if definition is None:
            raise ServiceResolutionError(f"unknown service id: {service_id}")
        enabled = service_id in salon_config.enabled_service_ids
        unresolved = tuple(cid for cid in definition.component_service_ids if cid not in salon_config.enabled_service_ids)
        return ServiceResolution(
            requested_id=service_id,
            definition=definition,
            salon_enabled=enabled,
            unresolved_component_ids=unresolved,
        )

    def require_executable_capability(self, resolution: ServiceResolution) -> None:
        if not resolution.salon_enabled:
            raise ServiceResolutionError("service is not enabled for this salon")
        if resolution.unresolved_component_ids:
            raise ServiceResolutionError("controlled service has unavailable component capability")
