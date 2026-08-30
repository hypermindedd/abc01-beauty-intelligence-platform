from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class FailureCategory(StrEnum):
    INVALID_TRANSITION = "INVALID_TRANSITION"
    AGENT_NOT_ALLOWED = "AGENT_NOT_ALLOWED"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
    PROFESSIONAL_REVIEW_REQUIRED = "PROFESSIONAL_REVIEW_REQUIRED"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    RETRYABLE_DEPENDENCY = "RETRYABLE_DEPENDENCY"
    NON_RETRYABLE_DEPENDENCY = "NON_RETRYABLE_DEPENDENCY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    INTERNAL_INVARIANT = "INTERNAL_INVARIANT"


class FailureDisposition(StrEnum):
    RETRY = "RETRY"
    WAIT_FOR_HUMAN = "WAIT_FOR_HUMAN"
    FAIL_CLOSED = "FAIL_CLOSED"


class OrchestrationFailure(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: FailureCategory
    disposition: FailureDisposition
    code: str
    detail: str = ""
    retryable: bool = False
