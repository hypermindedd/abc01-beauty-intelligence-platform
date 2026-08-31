from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class MediaConsentState(StrEnum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"


class VisualInputQuality(StrEnum):
    STRONG = "STRONG"
    USABLE = "USABLE"
    LIMITED = "LIMITED"
    UNREADABLE = "UNREADABLE"


class EditRegion(StrEnum):
    HAIR = "HAIR"
    HAIR_COLOR = "HAIR_COLOR"
    FACIAL_HAIR = "FACIAL_HAIR"
    MAKEUP_FACE = "MAKEUP_FACE"
    MAKEUP_EYES = "MAKEUP_EYES"
    MAKEUP_LIPS = "MAKEUP_LIPS"
    NAILS_LEFT = "NAILS_LEFT"
    NAILS_RIGHT = "NAILS_RIGHT"


class VisualPreviewRequest(BaseModel):
    """Provider-dispatch candidate. This is not a generated Preview or execution clearance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    service_ids: tuple[str, ...]
    requested_edit_regions: tuple[EditRegion, ...]
    source_media_consent: MediaConsentState = MediaConsentState.UNKNOWN
    provider_processing_consent: MediaConsentState = MediaConsentState.UNKNOWN
    input_quality: VisualInputQuality = VisualInputQuality.UNREADABLE

    @field_validator("service_ids")
    @classmethod
    def services_must_be_nonempty_and_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("visual preview request requires at least one governed service id")
        if len(set(value)) != len(value):
            raise ValueError("visual preview service ids must be unique")
        return value

    @field_validator("requested_edit_regions")
    @classmethod
    def edit_regions_must_be_unique(cls, value: tuple[EditRegion, ...]) -> tuple[EditRegion, ...]:
        if len(set(value)) != len(value):
            raise ValueError("requested edit regions must be unique")
        return value
