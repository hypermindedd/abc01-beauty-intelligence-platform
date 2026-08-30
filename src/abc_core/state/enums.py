from __future__ import annotations

from enum import StrEnum


class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    CLIENT = "CLIENT"
    SPECIALIST = "SPECIALIST"
    SALON_ADMIN = "SALON_ADMIN"
    VISUAL_RUNTIME = "VISUAL_RUNTIME"
    OUTPUT_COMPILER = "OUTPUT_COMPILER"


class EvidenceClass(StrEnum):
    KNOWN = "KNOWN"
    OBSERVED = "OBSERVED"
    USER_REPORTED = "USER_REPORTED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    REQUIRES_PROFESSIONAL_CHECK = "REQUIRES_PROFESSIONAL_CHECK"


class SafetyTier(StrEnum):
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"


class RecommendationRole(StrEnum):
    BEST_FIT = "BEST_FIT"
    ALTERNATIVE = "ALTERNATIVE"
    BOLDER = "BOLDER"


class PreviewStatus(StrEnum):
    REQUESTED = "REQUESTED"
    QUARANTINED = "QUARANTINED"
    QA_REJECTED = "QA_REJECTED"
    QA_APPROVED = "QA_APPROVED"


class SpecialistValidationStatus(StrEnum):
    NOT_REVIEWED = "NOT_REVIEWED"
    REQUIRES_CHECK = "REQUIRES_CHECK"
    PASSED = "PASSED"
    MODIFIED = "MODIFIED"
    DEFERRED = "DEFERRED"


class ServiceDecisionStatus(StrEnum):
    PROCEED = "PROCEED"
    MODIFY = "MODIFY"
    CHECK_FIRST = "CHECK_FIRST"
    DEFER = "DEFER"
    STOP = "STOP"
    UNRESOLVED = "UNRESOLVED"
