from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .failure import FailureCategory, OrchestrationFailure


class RetryDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    should_retry: bool
    next_attempt: int | None = None
    delay_ms: int | None = None
    reason: str


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_attempts: int = 3
    base_delay_ms: int = 250
    max_delay_ms: int = 2000

    def decide(self, failure: OrchestrationFailure, *, completed_attempts: int) -> RetryDecision:
        if completed_attempts < 1:
            raise ValueError("completed_attempts must be >= 1")
        retryable = (
            failure.retryable
            and failure.category is FailureCategory.RETRYABLE_DEPENDENCY
        )
        if not retryable:
            return RetryDecision(should_retry=False, reason="FAILURE_NOT_RETRYABLE")
        if completed_attempts >= self.max_attempts:
            return RetryDecision(should_retry=False, reason="RETRY_BUDGET_EXHAUSTED")
        delay = min(self.base_delay_ms * (2 ** (completed_attempts - 1)), self.max_delay_ms)
        return RetryDecision(
            should_retry=True,
            next_attempt=completed_attempts + 1,
            delay_ms=delay,
            reason="BOUNDED_RETRY_ALLOWED",
        )
