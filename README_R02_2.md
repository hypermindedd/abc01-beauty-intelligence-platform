# ABC.01 — R02.2 Canonical State / Object Model & Mutation Boundaries

R02.2 moves the R01.2 truth-state architecture into executable code. It retains the R02.1 Productization baseline gate and adds a typed, tenant-scoped canonical session aggregate with controlled mutation authority and append-only mutation events.

## Runtime invariants

- one canonical truth state; UI/LLM/output are projections, not truth;
- monotonic state revision on every accepted mutation;
- tenant mismatch fails closed;
- specialist review precedes ranked recommendations;
- client selection does not create Specialist Validation;
- only a specialist actor may mutate Specialist Validation or make a service decision;
- unresolved S2/S3 blocks PROCEED;
- Decision Preview cannot establish feasibility, safety or service success;
- commercial eligibility does not reorder Core recommendations;
- Core roles remain BEST_FIT / ALTERNATIVE / BOLDER;
- Explore is optional 0–3 and cannot relabel Core; total active looks <= 6;
- AG-10 output compilation is projection-only and cannot mutate canonical truth.

## Non-claims

R02.2 remains an engineering implementation stage. It does not claim runtime product validation, pilot readiness or production readiness.
