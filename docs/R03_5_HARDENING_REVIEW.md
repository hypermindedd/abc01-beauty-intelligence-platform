# R03.5 — QA hardening review

Status: BLOCKED / NOT MERGEABLE BY GOVERNANCE. This record documents gaps in the current candidate and does not claim a fix or a successful retest.

## Verified source-level gaps

1. `required_dimensions_for_services` uses prefix matching. An unknown service ID can receive a plausible QA profile instead of failing closed.
2. Controlled-service requirements are not fully expanded from the exact canonical service registry. A complete look can omit a component's preservation obligations.
3. The QA engine compares a supplied composite digest with a supplied evidence digest but does not recompute the digest from the actual raster bytes. A forged or corrupted composite can therefore satisfy the metadata-only check.
4. QA evidence is bound only to composite ID/digest, not the full request, tenant, session, source, selected option, canonical revision and service scope.

## Required correction

Use exact canonical service resolution, reject unknown/forbidden/empty scope, inherit controlled-component obligations, validate actual raster byte length and SHA-256, and bind evidence to the full immutable context. Add negative regression tests and rerun the full R02/R03 suite before merge.

## Boundary

A passed engineering test does not establish live semantic-evaluator accuracy, real provider operation, production media persistence, automatic segmentation, Specialist Validation, Runtime Product PASS, Pilot Ready or Production Ready. These remain NO. No frozen Productization authority or service ontology is modified by this review.

Regression commit: `2a4944c000543cb9b40236ef8dfa12b10b925b02`.
