from __future__ import annotations

from dataclasses import dataclass, field

from abc_core.state.models import SalonSessionState

from .engine import OrchestratorEngine, OrchestrationRejected
from .failure import (
    FailureCategory,
    FailureDisposition,
    OrchestrationFailure,
)
from .idempotency import (
    IdempotencyConflict,
    IdempotencyOutcome,
    InMemoryIdempotencyLedger,
)
from .observability import (
    EventSink,
    InMemoryEventSink,
    OrchestrationEvent,
    OrchestrationEventType,
)
from .retry import RetryDecision, RetryPolicy


class OrchestrationControlError(RuntimeError):
    def __init__(self, failure: OrchestrationFailure):
        super().__init__(failure.code)
        self.failure = failure


@dataclass
class OrchestrationControlPlane:
    """Engineering control plane joining routing, idempotency, retry and telemetry.

    Durable ledger/event adapters intentionally remain out of scope until R02.4.
    """

    orchestrator: OrchestratorEngine = field(default_factory=OrchestratorEngine)
    idempotency: InMemoryIdempotencyLedger = field(default_factory=InMemoryIdempotencyLedger)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    events: EventSink = field(default_factory=InMemoryEventSink)

    def _emit(
        self,
        state: SalonSessionState,
        event_type: OrchestrationEventType,
        *,
        agent_id: str | None = None,
        idempotency_key: str | None = None,
        detail: str = "",
    ) -> None:
        phase = self.orchestrator.derive_phase(state)
        self.events.emit(
            OrchestrationEvent(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                revision=state.revision,
                event_type=event_type,
                phase=phase.value,
                agent_id=agent_id,
                idempotency_key=idempotency_key,
                detail=detail,
            )
        )

    def project(self, state: SalonSessionState):
        snapshot = self.orchestrator.snapshot(state)
        self._emit(state, OrchestrationEventType.PHASE_PROJECTED)
        return snapshot

    def authorize_agent(self, state: SalonSessionState, agent_id: str) -> None:
        try:
            self.orchestrator.require_agent_allowed(state, agent_id)
        except OrchestrationRejected as exc:
            self._emit(
                state,
                OrchestrationEventType.AGENT_REJECTED,
                agent_id=agent_id,
                detail=str(exc),
            )
            raise OrchestrationControlError(
                OrchestrationFailure(
                    category=FailureCategory.AGENT_NOT_ALLOWED,
                    disposition=FailureDisposition.FAIL_CLOSED,
                    code="ORCH_AGENT_NOT_ALLOWED",
                    detail=str(exc),
                )
            ) from exc
        self._emit(state, OrchestrationEventType.AGENT_ALLOWED, agent_id=agent_id)

    def accept_command(
        self,
        state: SalonSessionState,
        *,
        agent_id: str,
        idempotency_key: str,
        payload_fingerprint: str,
    ) -> IdempotencyOutcome:
        self.authorize_agent(state, agent_id)
        try:
            outcome = self.idempotency.register(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                idempotency_key=idempotency_key,
                payload_fingerprint=payload_fingerprint,
            )
        except IdempotencyConflict as exc:
            self._emit(
                state,
                OrchestrationEventType.IDEMPOTENCY_CONFLICT,
                agent_id=agent_id,
                idempotency_key=idempotency_key,
                detail=str(exc),
            )
            raise OrchestrationControlError(
                OrchestrationFailure(
                    category=FailureCategory.IDEMPOTENCY_CONFLICT,
                    disposition=FailureDisposition.FAIL_CLOSED,
                    code="ORCH_IDEMPOTENCY_CONFLICT",
                    detail=str(exc),
                )
            ) from exc

        event_type = (
            OrchestrationEventType.IDEMPOTENCY_ACCEPTED
            if outcome is IdempotencyOutcome.ACCEPTED
            else OrchestrationEventType.IDEMPOTENCY_REPLAY
        )
        self._emit(
            state,
            event_type,
            agent_id=agent_id,
            idempotency_key=idempotency_key,
        )
        return outcome

    def retry_decision(
        self,
        state: SalonSessionState,
        failure: OrchestrationFailure,
        *,
        completed_attempts: int,
    ) -> RetryDecision:
        decision = self.retry_policy.decide(
            failure,
            completed_attempts=completed_attempts,
        )
        event_type = (
            OrchestrationEventType.RETRY_SCHEDULED
            if decision.should_retry
            else OrchestrationEventType.RETRY_EXHAUSTED
        )
        self._emit(state, event_type, detail=decision.reason)
        return decision
