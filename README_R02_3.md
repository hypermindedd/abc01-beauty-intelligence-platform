# ABC.01 — R02.3 Orchestrator & Workflow State Machine

R02.3 implements AG-01 as a deterministic workflow projector over the single canonical `SalonSessionState` established in R02.2. The orchestrator does not create a second truth store and does not mutate canonical state while computing workflow phase, blockers, allowed agents or next actions.

## Canonical consultation phases

`SPECIALIST_SETUP → CLIENT_GUIDED_INPUT → ANALYSIS_REVIEW → SHARED_REVIEW → SPECIALIST_VALIDATION → SERVICE_CONFIRMATION → COMPLETE`

## Runtime invariants

- workflow phase is derived from canonical state revision;
- no separate mutable workflow truth exists;
- agent dispatch is phase allowlisted and fails closed;
- unresolved S2/S3 Safety state is surfaced as an orchestration blocker;
- specialist analysis review remains required before ranked recommendation;
- client selection remains distinct from Specialist Validation;
- `CHECK_FIRST` / `UNRESOLVED` do not become terminal completion;
- only a legitimate service decision can close the consultation workflow;
- AG-01 routing does not override AG-03/04/05/07/08 semantic ownership.

## Non-claims

R02.3 remains an engineering implementation stage. It does not claim runtime product validation, visual-runtime validation, pilot readiness or production readiness.
