from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class QaDimension(StrEnum):
    REQUESTED_CHANGE_FIDELITY = "REQUESTED_CHANGE_FIDELITY"
    IDENTITY_CONTINUITY = "IDENTITY_CONTINUITY"
    FACE_GEOMETRY_CONTINUITY = "FACE_GEOMETRY_CONTINUITY"
    HAND_GEOMETRY_CONTINUITY = "HAND_GEOMETRY_CONTINUITY"
    FACIAL_HAIR_SOURCE_REALITY = "FACIAL_HAIR_SOURCE_REALITY"
    HAIR_SHAPE_SOURCE_REALITY = "HAIR_SHAPE_SOURCE_REALITY"
    UNRELATED_REGION_INTEGRITY = "UNRELATED_REGION_INTEGRITY"
    DOMAIN_SOURCE_REALITY = "DOMAIN_SOURCE_REALITY"


class QaFindingStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    REQUIRES_SPECIALIST_CHECK = "REQUIRES_SPECIALIST_CHECK"


class QaEvidenceOrigin(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    MODEL_EVALUATION = "MODEL_EVALUATION"
    SPECIALIST_REVIEW = "SPECIALIST_REVIEW"


@dataclass(frozen=True)
class QaFinding:
    dimension: QaDimension
    status: QaFindingStatus
    rationale: str
    origin: QaEvidenceOrigin

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("QA finding rationale must not be empty")


@dataclass(frozen=True)
class VisualQaEvidenceBundle:
    composite_id: str
    composite_pixel_sha256: str
    findings: tuple[QaFinding, ...]
    request_id: str = ""
    tenant_id: str = ""
    session_id: str = ""
    source_asset_id: str = ""
    option_id: str = ""
    canonical_revision: int = -1
    service_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        digest = self.composite_pixel_sha256.lower()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("composite_pixel_sha256 must be a 64-character hexadecimal digest")
        if len({finding.dimension for finding in self.findings}) != len(self.findings):
            raise ValueError("QA evidence contains duplicate dimensions")
        if self.canonical_revision < 0:
            raise ValueError("QA evidence canonical_revision must be non-negative")
        if not self.service_ids or len(set(self.service_ids)) != len(self.service_ids):
            raise ValueError("QA evidence service_ids must be nonempty and unique")
        object.__setattr__(self, "composite_pixel_sha256", digest)


@dataclass(frozen=True)
class RetryBudget:
    attempt: int
    max_attempts: int = 2

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.max_attempts > 3:
            raise ValueError("QA retry budget must be between 1 and 3 attempts")
        if self.attempt < 1 or self.attempt > self.max_attempts:
            raise ValueError("QA attempt must be inside the bounded retry budget")

    @property
    def retry_available(self) -> bool:
        return self.attempt < self.max_attempts
