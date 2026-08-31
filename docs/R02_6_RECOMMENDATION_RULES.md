# R02.6 — Recommendation Runtime Governance

Status: ENGINEERING RULESET — NOT PILOT/PRODUCTION READY

## Hard laws

1. Ranked recommendations require a sufficient governed capture and specialist-reviewed analysis.
2. Invalid candidates are filtered before ranking; ranking never legitimizes an invalid candidate.
3. Core roles are ordered semantics: BEST_FIT, ALTERNATIVE, BOLDER.
4. Core contains 1–3 valid materially distinct directions. Three is a maximum target, never a filler quota.
5. Explore contains 0–3 additional materially distinct directions and is explicit-only.
6. Fixed Choice never auto-expands into Explore.
7. Named style libraries are reference vocabulary, not the recommendation boundary; custom/composite directions are first-class.
8. Every component retains its service owner and must carry evidence-grounded rationale.
9. Source-reality requirements fail closed when the required source state is missing or incompatible.
10. Structural duplicates cannot occupy separate recommendation slots.
11. Commercial entitlement may expand exploration/revision allowance but cannot change Best Fit quality, Safety, evidence quality floor or Specialist Validation.
12. Client Selection is not Specialist Validation and cannot become Service Decision clearance.

## Known integration consistency gate

The pre-R02.6 canonical state mutation contract currently requires exactly three core options. R02.6 changes the product invariant to 1–3 valid core directions to enforce NO_FILLER. The canonical mutation path must be reconciled before R02.6 can be closed or merged.

## Non-claims

- No live recommendation-provider quality validation.
- No Pilot Ready claim.
- No Production Ready claim.
