from __future__ import annotations

from dataclasses import dataclass, field

from .models import InfrastructureCapability, InfrastructureStatus


class InfrastructureUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class InfrastructureTruth:
    """Truthful adapter capability state for R02.4.

    Interfaces existing in source code do not imply configured or verified
    production infrastructure. The default therefore remains INTERFACE_ONLY.
    """

    statuses: dict[InfrastructureCapability, InfrastructureStatus] = field(
        default_factory=lambda: {
            InfrastructureCapability.AUTH: InfrastructureStatus.INTERFACE_ONLY,
            InfrastructureCapability.PERSISTENCE: InfrastructureStatus.INTERFACE_ONLY,
            InfrastructureCapability.SECRETS: InfrastructureStatus.INTERFACE_ONLY,
            InfrastructureCapability.SALON_CONFIG: InfrastructureStatus.INTERFACE_ONLY,
        }
    )

    def status(self, capability: InfrastructureCapability) -> InfrastructureStatus:
        return self.statuses.get(capability, InfrastructureStatus.UNAVAILABLE)

    def is_verified(self, capability: InfrastructureCapability) -> bool:
        return self.status(capability) is InfrastructureStatus.VERIFIED

    def require_verified(self, capability: InfrastructureCapability) -> None:
        status = self.status(capability)
        if status is not InfrastructureStatus.VERIFIED:
            raise InfrastructureUnavailable(
                f"{capability} is {status}; VERIFIED adapter required"
            )

    def public(self) -> dict[str, str]:
        return {
            capability.value: self.status(capability).value
            for capability in InfrastructureCapability
        }


INFRASTRUCTURE = InfrastructureTruth()
