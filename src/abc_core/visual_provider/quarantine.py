from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ArtifactTrust(StrEnum):
    UNTRUSTED = "UNTRUSTED"


class QuarantineDisposition(StrEnum):
    HOLD = "HOLD"
    REJECTED = "REJECTED"


class RawArtifactNotPublishable(RuntimeError):
    pass


@dataclass(frozen=True)
class QuarantinedProviderArtifact:
    """Raw provider output. It is deliberately not a Decision Preview."""

    quarantine_id: str
    dispatch_id: str
    dispatch_fingerprint: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    canonical_revision: int
    provider_adapter_id: str
    provider_claimed_id: str
    provider_request_id: str
    mask_id: str
    mask_sha256: str
    authorization_sha256: str
    source_sha256: str
    raw_sha256: str
    media_type: str
    byte_length: int
    disposition: QuarantineDisposition
    rejection_reasons: tuple[str, ...] = ()
    trust: ArtifactTrust = ArtifactTrust.UNTRUSTED
    direct_preview_publishable: bool = False
    payload: bytes = field(default=b"", repr=False, compare=False)

    def require_preview_publishable(self) -> None:
        raise RawArtifactNotPublishable(
            "raw provider output is quarantined and cannot become a Decision Preview directly"
        )


class InMemoryRawOutputQuarantine:
    """Non-durable engineering quarantine. Durable media storage is not claimed."""

    durable = False

    def __init__(self) -> None:
        self._records: dict[str, QuarantinedProviderArtifact] = {}

    def put(self, artifact: QuarantinedProviderArtifact) -> None:
        existing = self._records.get(artifact.quarantine_id)
        if existing is not None and existing != artifact:
            raise RuntimeError("quarantine id collision")
        self._records[artifact.quarantine_id] = artifact

    def get(self, quarantine_id: str) -> QuarantinedProviderArtifact | None:
        return self._records.get(quarantine_id)

    def records(self) -> tuple[QuarantinedProviderArtifact, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def __len__(self) -> int:
        return len(self._records)
