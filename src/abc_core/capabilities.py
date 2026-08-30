from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CapabilityState:
    production_auth: bool = False
    production_persistence: bool = False
    external_visual_provider: bool = False
    deterministic_full_frame_lock_compositor: bool = False
    live_cross_domain_validation: bool = False
    pilot_ready: bool = False
    production_ready: bool = False

    def public(self) -> dict[str, bool]:
        return asdict(self)


CAPABILITIES = CapabilityState()
