from abc_core.orchestration import (
    FailureCategory,
    FailureDisposition,
    IdempotencyOutcome,
    InMemoryEventSink,
    OrchestrationControlError,
    OrchestrationControlPlane,
    OrchestrationEventType,
    OrchestrationFailure,
)
from abc_core.state.models import SalonSessionState


def state():
    return SalonSessionState(tenant_id="tenant-1", session_id="session-1")


def test_idempotent_replay_is_distinct_from_first_acceptance():
    sink = InMemoryEventSink()
    control = OrchestrationControlPlane(events=sink)
    s = state()

    first = control.accept_command(
        s,
        agent_id="AG-02",
        idempotency_key="cmd-1",
        payload_fingerprint="sha256:aaa",
    )
    replay = control.accept_command(
        s,
        agent_id="AG-02",
        idempotency_key="cmd-1",
        payload_fingerprint="sha256:aaa",
    )

    assert first is IdempotencyOutcome.ACCEPTED
    assert replay is IdempotencyOutcome.REPLAY
    assert OrchestrationEventType.IDEMPOTENCY_ACCEPTED in [e.event_type for e in sink.events]
    assert OrchestrationEventType.IDEMPOTENCY_REPLAY in [e.event_type for e in sink.events]


def test_idempotency_conflict_fails_closed():
    control = OrchestrationControlPlane()
    s = state()
    control.accept_command(
        s,
        agent_id="AG-02",
        idempotency_key="cmd-1",
        payload_fingerprint="sha256:aaa",
    )
    try:
        control.accept_command(
            s,
            agent_id="AG-02",
            idempotency_key="cmd-1",
            payload_fingerprint="sha256:bbb",
        )
    except OrchestrationControlError as exc:
        assert exc.failure.category is FailureCategory.IDEMPOTENCY_CONFLICT
        assert exc.failure.disposition is FailureDisposition.FAIL_CLOSED
    else:
        raise AssertionError("idempotency conflict must fail closed")


def test_idempotency_scope_is_tenant_and_session_specific():
    control = OrchestrationControlPlane()
    a = SalonSessionState(tenant_id="tenant-a", session_id="same")
    b = SalonSessionState(tenant_id="tenant-b", session_id="same")
    assert control.accept_command(
        a,
        agent_id="AG-02",
        idempotency_key="key",
        payload_fingerprint="sha256:a",
    ) is IdempotencyOutcome.ACCEPTED
    assert control.accept_command(
        b,
        agent_id="AG-02",
        idempotency_key="key",
        payload_fingerprint="sha256:b",
    ) is IdempotencyOutcome.ACCEPTED


def test_non_allowlisted_agent_is_typed_failure_and_observable():
    sink = InMemoryEventSink()
    control = OrchestrationControlPlane(events=sink)
    try:
        control.authorize_agent(state(), "AG-09")
    except OrchestrationControlError as exc:
        assert exc.failure.category is FailureCategory.AGENT_NOT_ALLOWED
    else:
        raise AssertionError("agent routing must fail closed")
    assert sink.events[-1].event_type is OrchestrationEventType.AGENT_REJECTED


def test_retry_policy_is_bounded_and_only_for_retryable_dependency_failure():
    sink = InMemoryEventSink()
    control = OrchestrationControlPlane(events=sink)
    failure = OrchestrationFailure(
        category=FailureCategory.RETRYABLE_DEPENDENCY,
        disposition=FailureDisposition.RETRY,
        code="TEMP_PROVIDER_TIMEOUT",
        retryable=True,
    )
    d1 = control.retry_decision(state(), failure, completed_attempts=1)
    d2 = control.retry_decision(state(), failure, completed_attempts=2)
    d3 = control.retry_decision(state(), failure, completed_attempts=3)
    assert d1.should_retry and d1.next_attempt == 2 and d1.delay_ms == 250
    assert d2.should_retry and d2.next_attempt == 3 and d2.delay_ms == 500
    assert d3.should_retry is False and d3.reason == "RETRY_BUDGET_EXHAUSTED"
    assert sink.events[-1].event_type is OrchestrationEventType.RETRY_EXHAUSTED


def test_safety_or_human_failures_never_enter_automatic_retry():
    control = OrchestrationControlPlane()
    failure = OrchestrationFailure(
        category=FailureCategory.PROFESSIONAL_REVIEW_REQUIRED,
        disposition=FailureDisposition.WAIT_FOR_HUMAN,
        code="SPECIALIST_CHECK_REQUIRED",
        retryable=False,
    )
    decision = control.retry_decision(state(), failure, completed_attempts=1)
    assert decision.should_retry is False
    assert decision.reason == "FAILURE_NOT_RETRYABLE"


def test_observability_projection_does_not_change_canonical_state():
    sink = InMemoryEventSink()
    control = OrchestrationControlPlane(events=sink)
    s = state()
    before = s.canonical_snapshot()
    snapshot = control.project(s)
    assert snapshot.revision == 0
    assert s.canonical_snapshot() == before
    assert sink.events[-1].revision == 0
    assert sink.events[-1].event_type is OrchestrationEventType.PHASE_PROJECTED
