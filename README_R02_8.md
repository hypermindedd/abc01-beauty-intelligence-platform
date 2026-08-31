# ABC.01 R02.8 — Integrated Core Gate

Status: engineering closeout candidate; not a runtime-product, pilot, production, or live-visual readiness claim.

## Gate objective

R02.8 verifies that the available cross-domain Core composes coherently from one canonical `SalonSessionState` across capture/analysis, specialist review, recommendation, service intelligence, safety and output projection. Infrastructure or visual capabilities that do not exist are reported as `UNAVAILABLE`, never simulated into PASS.

## Covered matrix

- Hair — SVC-01
- Hair Color — SVC-02
- Makeup — SVC-03
- Nails — SVC-04
- Men's Hair / Beard — SVC-05
- Bridal / Complete Look — CTRL-009 with explicit required component capability
- Controlled Service — CTRL-007 baseline S2 path

## Hard checks

- governed domain capture plan is present in canonical analysis state;
- ranked recommendation requires sufficient, specialist-reviewed analysis;
- at least one valid Core direction exists and canonical recommendation rules remain enforced;
- AG-06 resolves exact service/capability semantics and fails closed for unknown/forbidden IDs;
- AG-08 merges service-baseline and canonical session safety;
- an existing Service Decision must be permitted by the integrated safety assessment;
- AG-10 Shared projection hides raw runtime identifiers and specialist-only details;
- Shared safety attention reflects integrated baseline + session safety;
- booking/payment completion remains false unless a real action layer exists;
- QA-approved Preview is rejected while required external visual/compositor capabilities are unavailable;
- the integrated gate and AG-06→08→10 compilation are read-only against canonical truth.

## Capability honesty at R02.8

The current Core explicitly reports these capabilities unavailable:

- production auth
- production persistence
- external visual provider
- deterministic full-frame lock compositor
- live cross-domain validation
- pilot readiness
- production readiness

These are not R02.8 failures because their implementation belongs to later infrastructure/visual/release stages; false availability claims would be failures.

## Validation evidence

Implementation head: `51cd4fb0de2332d13d9bd144de4b209c8458db78`

GitHub Actions run: `33376809408`

Result: `PASS`

Test result: `99 passed, 1 deprecation warning, 0 failed` on Python 3.13.

The warning is dependency-level Starlette/httpx deprecation and is not a test failure.

## Non-claims

- Runtime Product PASS: NO
- Live cross-domain validation: NO
- External visual runtime validated: NO
- Pilot Ready: NO
- Production Ready: NO

R03 may begin only after R02.8 PR checks, merge, post-merge main CI and governance reconciliation succeed.