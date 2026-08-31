from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from abc_core.visual_request import EditRegion


class MaskMode(StrEnum):
    AUTO = "AUTO"
    SPECIALIST_ASSISTED = "SPECIALIST_ASSISTED"
    HYBRID = "HYBRID"


class FrameLockPolicy(StrEnum):
    FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION = (
        "FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION"
    )


class MaskSpan(BaseModel):
    """One half-open horizontal run of active mask pixels: [x_start, x_end)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    y: int = Field(ge=0)
    x_start: int = Field(ge=0)
    x_end: int = Field(gt=0)

    @model_validator(mode="after")
    def end_must_follow_start(self):
        if self.x_end <= self.x_start:
            raise ValueError("mask span x_end must be greater than x_start")
        return self


class RegionMask(BaseModel):
    """Exact binary mask geometry for one semantic edit region, encoded as spans."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    region: EditRegion
    spans: tuple[MaskSpan, ...]

    @field_validator("spans")
    @classmethod
    def spans_must_not_be_empty(cls, value: tuple[MaskSpan, ...]) -> tuple[MaskSpan, ...]:
        if not value:
            raise ValueError("region mask must contain active pixels")
        return value


class MaskAuthorization(BaseModel):
    """Governed pixel authorization for one visual request/source frame."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    authorization_id: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    region_masks: tuple[RegionMask, ...]
    policy: FrameLockPolicy = FrameLockPolicy.FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION

    @field_validator("region_masks")
    @classmethod
    def authorization_regions_must_be_unique(cls, value: tuple[RegionMask, ...]) -> tuple[RegionMask, ...]:
        if not value:
            raise ValueError("mask authorization must contain at least one region")
        regions = [item.region for item in value]
        if len(regions) != len(set(regions)):
            raise ValueError("mask authorization regions must be unique")
        return value


class MaskCandidate(BaseModel):
    """Untrusted mask candidate produced by AUTO, specialist-assisted, or HYBRID acquisition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mask_id: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    mode: MaskMode
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    region_masks: tuple[RegionMask, ...]
    mask_sha256: str
    specialist_actor_id: str | None = None

    @field_validator("region_masks")
    @classmethod
    def candidate_regions_must_be_unique(cls, value: tuple[RegionMask, ...]) -> tuple[RegionMask, ...]:
        if not value:
            raise ValueError("mask candidate must contain at least one region")
        regions = [item.region for item in value]
        if len(regions) != len(set(regions)):
            raise ValueError("mask candidate regions must be unique")
        return value

    @field_validator("mask_sha256")
    @classmethod
    def sha256_must_be_hex(cls, value: str) -> str:
        normalized = value.lower()
        if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
            raise ValueError("mask_sha256 must be a 64-character hexadecimal digest")
        return normalized

    @model_validator(mode="after")
    def assisted_modes_require_specialist_provenance(self):
        if self.mode in {MaskMode.SPECIALIST_ASSISTED, MaskMode.HYBRID} and not self.specialist_actor_id:
            raise ValueError("specialist-assisted and hybrid masks require specialist_actor_id")
        return self
