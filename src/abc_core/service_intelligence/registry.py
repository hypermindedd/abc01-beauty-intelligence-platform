from __future__ import annotations

from abc_core.state import SafetyTier
from .contracts import ServiceDefinition


def _family(prefix: str, count: int, owner: tuple[str, ...], safety: SafetyTier) -> dict[str, ServiceDefinition]:
    return {
        f"{prefix}-{i:03d}": ServiceDefinition(
            service_id=f"{prefix}-{i:03d}", family=prefix, knowledge_owners=owner, baseline_safety=safety
        ) for i in range(1, count + 1)
    }


SERVICE_REGISTRY: dict[str, ServiceDefinition] = {}
SERVICE_REGISTRY.update(_family("SVC-01", 7, ("ABC-KB-003",), SafetyTier.S0))
SERVICE_REGISTRY.update(_family("SVC-02", 9, ("ABC-KB-004",), SafetyTier.S1))
SERVICE_REGISTRY.update(_family("SVC-03", 7, ("ABC-KB-005",), SafetyTier.S0))
SERVICE_REGISTRY.update(_family("SVC-04", 7, ("ABC-KB-006",), SafetyTier.S0))
SERVICE_REGISTRY.update(_family("SVC-05", 9, ("ABC-KB-007", "ABC-KB-008"), SafetyTier.S0))

# Exact authority exceptions and controlled-service ownership. No prefix guessing is permitted at runtime.
SERVICE_REGISTRY["SVC-01-007"] = ServiceDefinition("SVC-01-007", "SVC-01", ("ABC-KB-013",), SafetyTier.S2, True)

CONTROLLED: dict[str, ServiceDefinition] = {
    "CTRL-001": ServiceDefinition("CTRL-001", "CONTROLLED", ("ABC-KB-003","ABC-KB-009"), SafetyTier.S0, True, ("SVC-01-006",)),
    "CTRL-002": ServiceDefinition("CTRL-002", "CONTROLLED", ("ABC-KB-005","ABC-KB-009"), SafetyTier.S0, True, ("SVC-03-005",)),
    "CTRL-003": ServiceDefinition("CTRL-003", "CONTROLLED", ("ABC-KB-006","ABC-KB-009"), SafetyTier.S0, True, ("SVC-04-007",)),
    "CTRL-004": ServiceDefinition("CTRL-004", "CONTROLLED", ("ABC-KB-007","ABC-KB-008","ABC-KB-009"), SafetyTier.S0, True, ("SVC-05-009",)),
    "CTRL-005": ServiceDefinition("CTRL-005", "CONTROLLED", ("ABC-KB-004",), SafetyTier.S1, True, ("SVC-02-009",)),
    "CTRL-006": ServiceDefinition("CTRL-006", "CONTROLLED", ("ABC-KB-013",), SafetyTier.S2, True, ("SVC-01-007",)),
    "CTRL-007": ServiceDefinition("CTRL-007", "CONTROLLED", ("ABC-KB-014",), SafetyTier.S2, True),
    "CTRL-008": ServiceDefinition("CTRL-008", "CONTROLLED", ("ABC-KB-005",), SafetyTier.S0, True, ("SVC-03-006",)),
    "CTRL-009": ServiceDefinition("CTRL-009", "CONTROLLED", ("ABC-KB-003","ABC-KB-005","ABC-KB-006","ABC-KB-009"), SafetyTier.S1, True, ("SVC-01-006","SVC-03-005","SVC-04-007"), True),
    "CTRL-010": ServiceDefinition("CTRL-010", "CONTROLLED", ("ABC-KB-006",), SafetyTier.S0, True, ("SVC-04-002",)),
}
SERVICE_REGISTRY.update(CONTROLLED)

FORBIDDEN_SERVICE_IDS = frozenset({"SVC-03-008", "CTRL-011", "CTRL-012", "CTRL-013"})
