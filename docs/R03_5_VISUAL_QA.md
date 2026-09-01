# ABC.01 R03.5 — Downstream Visual QA / Bounded Retry & Reject

Status: engineering implementation candidate. No live-provider, runtime-product, pilot or production readiness claim.

## Objective

R03.5 is the semantic QA boundary after R03.4 deterministic locked composition. It cannot weaken or replace R03.4 byte-exact outside-mask integrity. It evaluates whether the authorized change itself remains compatible with the requested direction and the source-reality obligations of the active service scope.

## Input boundary

Only an intact R03.4 `LockedCompositeArtifact` may be evaluated. QA evidence is bound to the exact `composite_id` and `composite_pixel_sha256`; evidence from another or stale composite fails closed.

R03.5 does not fabricate visual observations. It consumes explicit findings from a governed evaluator source such as deterministic checks, model evaluation, specialist review, or a controlled combination. Missing evidence is not PASS.

## Canonical QA dimensions

- requested-change fidelity;
- identity continuity where the service concerns the person/face/hair;
- face geometry continuity for makeup/grooming/full-look scopes;
- hand geometry continuity for nails;
- facial-hair source reality for men’s hair/beard services;
- hair-shape source reality for hair/hair-color/grooming/full-look scopes;
- unrelated-region integrity;
- domain source reality.

The requirement set is additive for multi-service requests.

## Result semantics

`QA_APPROVED`
: every required dimension has explicit PASS evidence. The artifact becomes eligible only as a Decision Preview candidate; this engine does not mutate canonical session state or claim Specialist Validation.

`RETRY`
: at least one required dimension FAILS and a bounded retry remains.

`REJECT`
: failure remains after the final allowed attempt, or QA evidence is bound to the wrong composite.

`HONEST_LIMITATION`
: a required finding is missing or UNKNOWN. No fabricated confidence or inferred PASS.

`SPECIALIST_CHECK`
: a required dimension explicitly requires professional review. AI cannot convert this state into PASS.

## Bounded retry

Default maximum is two attempts; the contract allows at most three if separately configured. Infinite regeneration is structurally rejected.

## Domain source-reality examples

- Hair Color: color changes may not silently change cut/length/shape.
- Makeup: face anatomy/geometry must remain stable.
- Nails: hand/finger geometry must remain stable.
- Men’s Hair / Beard: beard coverage or hair length must not be fabricated as a same-day result.

## Relationship to R03.4

Outside the exact edit mask, R03.4 remains authoritative through byte-exact source lock. R03.5 focuses on semantic integrity and requested-change correctness, especially inside the authorized region and across service-specific source-reality constraints.

## Non-claims

- live semantic evaluator validated against paid provider outputs: NO
- real external provider execution validated: NO
- automatic segmentation: NO
- production media persistence: NO
- live cross-domain visual validation: NO
- Runtime Product PASS: NO
- Pilot Ready: NO
- Production Ready: NO
