# ABC.01 R03.1 — Visual Request & Capability Gate

Status: engineering implementation candidate. This stage does not call an external image provider and does not claim a validated visual runtime.

## Objective

R03.1 creates the fail-closed boundary that must pass before any external visual provider dispatch. It consumes the closed R02.8 canonical Core and adds no second mutable session truth.

## Required order

`Preview Request → Tenant/Config Gate → Capability Gate → Safety Gate → Media/Consent Gate → Input Quality Gate → Edit Scope Authorization → Dispatch Eligibility`

Provider dispatch is allowed only when every R03.1 gate passes.

## Hard rules

- request tenant and session must match canonical `SalonSessionState`;
- requested services must remain inside the canonical session request and the tenant-enabled service set;
- `VISUAL_PREVIEW` must be explicitly enabled in salon configuration;
- source asset must already exist in canonical session inputs and be image media;
- Preview must reference the currently client-selected active recommendation direction;
- source-media consent and provider-processing consent must both be explicitly `GRANTED`;
- image quality must be `USABLE` or `STRONG`;
- requested edit regions must be non-empty and a subset of externally supplied governed authorization; the gate does not guess service→region policy;
- unresolved S2/S3 professional safety checks block provider dispatch at this engineering boundary;
- external provider capability and deterministic full-frame-lock compositor capability must both be available before dispatch is permitted;
- current global capability truth keeps both capabilities `false`, so production/provider dispatch remains blocked by default;
- the gate is pure/read-only and may not mutate canonical session state;
- passing this gate is not Preview QA, Specialist Validation, service clearance, Pilot Ready, Production Ready or Runtime Product PASS.

## Why compositor availability is checked before provider dispatch

Raw provider output is untrusted quarantine material, never the final Decision Preview. R03.1 therefore refuses to spend a provider call when the mandatory deterministic post-provider lock/compositor path is unavailable. This prevents a later layer from silently publishing unconstrained raw output.

## Current non-claims

- external provider implementation validated: NO
- deterministic full-frame lock compositor implemented/validated: NO
- mask acquisition/validation implemented: NO
- provider quarantine implemented in R03 production path: NO
- identity/source-reality visual QA validated: NO
- live cross-domain visual validation: NO
- Runtime Product PASS: NO
- Pilot Ready: NO
- Production Ready: NO

## Next stage after PASS

R03.2 should implement validated edit-scope/mask acquisition and mask validation without weakening the R03.1 dispatch gate. Provider invocation remains downstream of those controls and still cannot publish directly to Decision Preview.
