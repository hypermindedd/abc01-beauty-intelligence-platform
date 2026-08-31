from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from abc_core.state.enums import EvidenceClass


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Domain(StrEnum):
    HAIR = "HAIR"
    HAIR_COLOR = "HAIR_COLOR"
    MAKEUP = "MAKEUP"
    NAILS = "NAILS"
    MENS_HAIR_BEARD = "MENS_HAIR_BEARD"
    BRIDAL_GROOM = "BRIDAL_GROOM"
    CONTROLLED_SERVICE = "CONTROLLED_SERVICE"


class CaptureView(StrEnum):
    FRONT = "FRONT"
    LEFT_PROFILE = "LEFT_PROFILE"
    RIGHT_PROFILE = "RIGHT_PROFILE"
    BACK = "BACK"
    TOP = "TOP"
    DETAIL = "DETAIL"
    HANDS = "HANDS"
    NAIL_DETAIL = "NAIL_DETAIL"
    EXISTING_COLOR_DETAIL = "EXISTING_COLOR_DETAIL"


class ImageQuality(StrEnum):
    UNUSABLE = "UNUSABLE"
    LIMITED = "LIMITED"
    USABLE = "USABLE"
    STRONG = "STRONG"


class FindingVisibility(StrEnum):
    SHARED = "SHARED"
    SPECIALIST_ONLY = "SPECIALIST_ONLY"


class CaptureRequirement(FrozenModel):
    requirement_id: str
    view: CaptureView
    min_count: int = Field(default=1, ge=1, le=6)
    required: bool = True
    purpose: str


class CapturePlan(FrozenModel):
    plan_id: str
    domains: tuple[Domain, ...]
    requirements: tuple[CaptureRequirement, ...]

    @field_validator("domains")
    @classmethod
    def domains_unique(cls, value: tuple[Domain, ...]) -> tuple[Domain, ...]:
        if not value or len(set(value)) != len(value):
            raise ValueError("capture plan domains must be non-empty and unique")
        return value

    @field_validator("requirements")
    @classmethod
    def requirements_unique(cls, value: tuple[CaptureRequirement, ...]) -> tuple[CaptureRequirement, ...]:
        ids = [item.requirement_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("capture requirement ids must be unique")
        return value


class CaptureInput(FrozenModel):
    asset_id: str
    view: CaptureView
    quality: ImageQuality


class CaptureAssessment(FrozenModel):
    plan_id: str
    sufficient: bool
    satisfied_requirement_ids: tuple[str, ...] = ()
    missing_requirement_ids: tuple[str, ...] = ()
    limited_requirement_ids: tuple[str, ...] = ()
    note: str = ""


class AnalysisFinding(FrozenModel):
    finding_id: str
    domain: Domain
    statement: str
    evidence_class: EvidenceClass
    source_asset_ids: tuple[str, ...] = ()
    source_evidence_ids: tuple[str, ...] = ()
    visibility: FindingVisibility = FindingVisibility.SHARED
    requires_professional_check: bool = False

    @model_validator(mode="after")
    def provenance_and_classification_are_consistent(self) -> "AnalysisFinding":
        if self.evidence_class is EvidenceClass.OBSERVED and not self.source_asset_ids:
            raise ValueError("OBSERVED finding requires at least one source asset")
        if self.evidence_class is EvidenceClass.USER_REPORTED and not self.source_evidence_ids:
            raise ValueError("USER_REPORTED finding requires source evidence")
        if self.evidence_class is EvidenceClass.UNKNOWN:
            if self.source_asset_ids or self.source_evidence_ids:
                raise ValueError("UNKNOWN finding cannot claim supporting sources")
        if self.evidence_class is EvidenceClass.REQUIRES_PROFESSIONAL_CHECK and not self.requires_professional_check:
            raise ValueError("professional-check finding must set requires_professional_check=true")
        return self


class AnalysisStrategy(FrozenModel):
    strategy_id: str
    summary: str
    constraints: tuple[str, ...] = ()
    priorities: tuple[str, ...] = ()


class BeautyAnalysisBundle(FrozenModel):
    analysis_id: str
    capture_assessment: CaptureAssessment
    findings: tuple[AnalysisFinding, ...]
    shared_summary: str
    specialist_summary: str
    strategy: AnalysisStrategy
    specialist_reviewed: bool = False
    specialist_reviewer_id: str | None = None

    @model_validator(mode="after")
    def review_requires_sufficient_capture(self) -> "BeautyAnalysisBundle":
        if self.specialist_reviewed and not self.capture_assessment.sufficient:
            raise ValueError("specialist-reviewed analysis requires sufficient capture")
        if self.specialist_reviewed and not self.specialist_reviewer_id:
            raise ValueError("reviewed analysis requires specialist reviewer id")
        if self.specialist_reviewer_id and not self.specialist_reviewed:
            raise ValueError("reviewer id cannot be present before specialist review")
        return self
