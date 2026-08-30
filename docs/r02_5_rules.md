# ABC.01 — R02.5 Evidence & Analysis Hard Rules

These rules are binding for the R02.5 engineering baseline and all downstream recommendation logic unless superseded through explicit governed change control.

1. **Analysis before recommendation.** No ranked recommendation may be emitted until the required analysis review gate is satisfied.
2. **Media proves only supported visible facts.** Images may support visible observations; they may not silently establish hidden history, health state, ethnicity, religion, personality, culture, sexual orientation, gender identity, or other private traits.
3. **Unknown stays unknown.** Missing information remains `UNKNOWN` unless explicitly user-reported, known from salon-controlled data, or marked `REQUIRES_PROFESSIONAL_CHECK`.
4. **Capture insufficiency fails closed.** A service-specific capture plan must be satisfied before the runtime may claim sufficient evidence for that analysis scope.
5. **Evidence provenance is mandatory.** Every material analysis finding carries evidence class and source references where applicable.
6. **Inference cannot masquerade as observation.** `INFERRED` findings remain distinguishable from `OBSERVED`, `KNOWN`, and `USER_REPORTED` findings.
7. **Shared and specialist views are projections, not separate truths.** They compile from the same canonical analysis state with different disclosure/detail levels.
8. **Safety state survives analysis.** Analysis may surface professional checks or constraints but may not erase or downgrade existing safety authority.
9. **No filler findings.** The system must not invent analysis statements merely to populate a template or achieve a target count.
10. **Service-adaptive evidence contracts.** Hair, Hair Color, Makeup, Nails, Men's Hair/Beard, Bridal/Groom coordination and controlled services may require different capture/evidence fields while remaining under one Core.
