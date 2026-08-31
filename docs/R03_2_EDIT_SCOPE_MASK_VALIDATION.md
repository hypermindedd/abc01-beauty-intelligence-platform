# ABC.01 R03.2 — Edit Scope / Mask Acquisition & Validation

Status: engineering implementation candidate. This stage validates exact mask geometry and provenance before visual-provider dispatch. It does not implement segmentation, call an image provider, composite an image, or publish a Decision Preview.

## Objective

R03.2 tightens R03.1 by making the semantic requested edit scope executable as an exact pixel authorization. A provider may be called only when both the R03.1 preflight and the R03.2 mask gate pass.

## Canonical sequence

`R03.1 Visual Request Gate → Mask Acquisition Candidate → Exact Pixel Authorization → Mask Validation → Provider Dispatch Authorization`

Provider invocation remains downstream and unavailable under the current global capability truth.

## Mask modes

- `AUTO`
- `SPECIALIST_ASSISTED`
- `HYBRID`

Specialist-assisted and hybrid candidates require `specialist_actor_id` provenance. The mode does not change pixel authorization rules.

## Lock policy

`FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION`

The validated mask is the only region a future provider/compositor path may treat as editable. Everything else remains locked by contract.

## Geometry representation

R03.2 uses exact binary horizontal spans rather than a loose bounding box. Each `MaskSpan` represents `[x_start, x_end)` on one row. This allows arbitrary-shaped masks while keeping the contract deterministic and provider-independent.

Both the governed authorization and the untrusted mask candidate are bound to:

- request ID
- tenant ID
- session ID
- source asset ID
- selected option ID
- source frame width/height
- semantic edit regions

## Hard validation rules

- R03.1 must have passed;
- the R03.1 decision must be bound to the same request/source/selection/service/edit-scope tuple;
- the canonical Core revision must not have changed since R03.1;
- authorization and candidate must bind to the same request/source/selection;
- candidate dimensions must match authorized source dimensions;
- authorization regions and candidate regions must exactly match requested edit regions;
- every span must remain inside the source frame;
- candidate spans may not overlap themselves;
- every candidate pixel must be a subset of the governed authorization for the same semantic region;
- candidate SHA-256 is deterministically recomputed from canonical mask content and provenance and must match;
- validation is read-only against canonical `SalonSessionState`.

## Output

A PASS returns a `ValidatedMask` containing request/source/selection bindings, canonical revision, dimensions, semantic regions, mask SHA-256, authorization SHA-256 and lock policy.

This `ValidatedMask` is an engineering dispatch prerequisite. It is not Safety clearance, Specialist Validation, service feasibility, Preview QA, or execution clearance.

## Fail-closed behavior

Any binding mismatch, stale Core revision, dimension mismatch, region mismatch, out-of-bounds geometry, overlapping candidate geometry, authorization escape, hash mismatch, or blocked R03.1 preflight prevents downstream provider dispatch.

## Current non-claims

- automatic segmentation implementation: NO
- specialist mask editor UI: NO
- external visual provider validated: NO
- deterministic compositor implemented/validated: NO
- locked-pixel verification implemented: NO
- provider quarantine implemented in the final R03 path: NO
- identity/source-reality visual QA validated: NO
- live cross-domain visual validation: NO
- Runtime Product PASS: NO
- Pilot Ready: NO
- Production Ready: NO

## Next valid stage after PASS

R03.3 should implement provider adapter quarantine and dispatch binding such that only an R03.2 `ValidatedMask` can authorize an external generation/edit call. Raw provider output must enter quarantine and must never become a Decision Preview directly.
