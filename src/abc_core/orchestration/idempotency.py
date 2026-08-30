from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class IdempotencyOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    REPLAY = "REPLAY"


class IdempotencyConflict(RuntimeError):
    pass


class IdempotencyRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    session_id: str
    idempotency_key: str
    payload_fingerprint: str


class InMemoryIdempotencyLedger:
    """Deterministic engineering ledger; durable adapter belongs to R02.4."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], IdempotencyRecord] = {}

    def register(
        self,
        *,
        tenant_id: str,
        session_id: str,
        idempotency_key: str,
        payload_fingerprint: str,
    ) -> IdempotencyOutcome:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        if not payload_fingerprint.strip():
            raise ValueError("payload_fingerprint is required")
        identity = (tenant_id, session_id, idempotency_key)
        prior = self._records.get(identity)
        if prior is None:
            self._records[identity] = IdempotencyRecord(
                tenant_id=tenant_id,
                session_id=session_id,
                idempotency_key=idempotency_key,
                payload_fingerprint=payload_fingerprint,
            )
            return IdempotencyOutcome.ACCEPTED
        if prior.payload_fingerprint == payload_fingerprint:
            return IdempotencyOutcome.REPLAY
        raise IdempotencyConflict(
            "idempotency key was reused with a different payload fingerprint"
        )
