from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from abc_core.visual_mask import FrameLockPolicy, MaskCandidate
from abc_core.visual_request import EditRegion


@dataclass(frozen=True)
class SourcePayload:
    """Ephemeral source bytes supplied by the media layer for one governed asset."""

    asset_id: str
    media_type: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.asset_id:
            raise ValueError("source payload requires asset_id")
        if not self.media_type.lower().startswith("image/"):
            raise ValueError("visual source payload must be an image")
        if not self.content:
            raise ValueError("visual source payload must not be empty")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True)
class ProviderDispatchEnvelope:
    """Provider-independent immutable dispatch contract after R03.1 + R03.2."""

    dispatch_id: str
    dispatch_fingerprint: str
    provider_id: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    source_media_type: str
    source_sha256: str
    option_id: str
    service_ids: tuple[str, ...]
    requested_edit_regions: tuple[EditRegion, ...]
    canonical_revision: int
    mask_id: str
    mask_sha256: str
    authorization_sha256: str
    mask_width: int
    mask_height: int
    lock_policy: FrameLockPolicy
    instruction: str
    instruction_sha256: str


@dataclass(frozen=True)
class ProviderRawResult:
    """Untrusted bytes returned by an injected visual-provider adapter."""

    provider_id: str
    provider_request_id: str
    media_type: str
    content: bytes
    metadata: tuple[tuple[str, str], ...] = ()


class VisualProviderAdapter(Protocol):
    """Provider-neutral adapter boundary. Implementations may call external services."""

    provider_id: str

    def dispatch(
        self,
        envelope: ProviderDispatchEnvelope,
        *,
        source: SourcePayload,
        mask: MaskCandidate,
    ) -> ProviderRawResult:
        ...
