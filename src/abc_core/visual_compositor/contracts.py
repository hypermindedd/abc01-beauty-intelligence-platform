from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RasterFrame:
    """Decoded interleaved raster pixels bound to one upstream byte artifact.

    R03.4 intentionally operates on decoded bytes without choosing an image codec.
    A codec adapter must prove `provenance_sha256` against the governed source/raw
    artifact before this frame is accepted.
    """

    width: int
    height: int
    channels: int
    pixels: bytes = field(repr=False)
    provenance_sha256: str

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("raster dimensions must be positive")
        if self.channels not in {3, 4}:
            raise ValueError("R03.4 supports RGB or RGBA rasters only")
        expected = self.width * self.height * self.channels
        if len(self.pixels) != expected:
            raise ValueError(f"raster byte length mismatch: expected {expected}, got {len(self.pixels)}")
        digest = self.provenance_sha256.lower()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("provenance_sha256 must be a 64-character hexadecimal digest")
        object.__setattr__(self, "provenance_sha256", digest)

    @property
    def pixel_sha256(self) -> str:
        return hashlib.sha256(self.pixels).hexdigest()


@dataclass(frozen=True)
class LockedCompositeArtifact:
    """Deterministic composite that is still NOT a Decision Preview."""

    composite_id: str
    quarantine_id: str
    dispatch_id: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    canonical_revision: int
    mask_id: str
    mask_sha256: str
    authorization_sha256: str
    source_sha256: str
    raw_sha256: str
    width: int
    height: int
    channels: int
    composite_pixel_sha256: str
    locked_pixel_verification_sha256: str
    edited_pixel_count: int
    locked_pixel_count: int
    direct_preview_publishable: bool = False
    pixels: bytes = field(default=b"", repr=False, compare=False)

    def require_preview_publishable(self) -> None:
        raise RuntimeError(
            "R03.4 locked composite is not a Decision Preview; downstream Visual QA is mandatory"
        )
