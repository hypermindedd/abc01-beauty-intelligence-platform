# ABC CORE RUNTIME v0.4.0 — Cross-Domain Engine Architecture

**Status:** `IMPLEMENTED — LOCAL_E2E_PASS — LIVE_CROSS_DOMAIN_PROVIDER_VALIDATION_PENDING`

**Scope:** Canonical ABC Core. This is not a Men's Salon-only patch.

## 1. Governing design

ABC is implemented as one governed intelligence core with salon/edition configuration layered above it.

```text
SALON / PRODUCT EDITION
        ↓
CANONICAL SERVICE RESOLUTION
        ↓
SERVICE PROFILE + KNOWLEDGE OWNER(S)
        ↓
PROFESSIONAL MULTI-VIEW CAPTURE PLAN
        ↓
MULTI-VIEW EVIDENCE / SOURCE REALITY
        ↓
AG-03 BEAUTY ANALYSIS
        ↓
ANALYSIS BRIEF + STRATEGY
        ↓
HARD ANALYSIS-REVIEW GATE
        ↓
AG-04 CUSTOM DIRECTION COMPOSER
        ↓
BEST FIT / ALTERNATIVE / BOLDER
        ↓
OPTIONAL EXPLORE
        ↓
AG-05 DOMAIN-SPECIFIC PREVIEW CONTRACT
        ↓
PROVIDER OUTPUT QUARANTINE
        ↓
VISUAL INTEGRITY QA / RETRY / REJECT
        ↓
AG-07 SPECIALIST VALIDATION
        ↓
SERVICE DECISION
```

The same semantic engine path is used by Men's Salon, women's/general hair, color, makeup, nails, bridal/combined looks, extensions and smoothing/keratin. Edition UIs may render different screens, but may not change Core truth, evidence semantics, Safety, canonical IDs or professional authority.

## 2. Current canonical service coverage

The v0.4 Core routes only currently governed ABC service families/controlled services:

- `SVC-01` Hair: general haircut/style, layered/textured, bob, blow-dry/styling, special-occasion hair, controlled bridal/formal hair, controlled extensions.
- `SVC-02` Hair Color: base color, root refresh, toner, highlights, lowlights, balayage, ombré/sombré, gray coverage, controlled color correction.
- `SVC-03` Makeup: natural, day, glam, formal/event, controlled bridal, controlled corrective/coverage, eye/brow/lip focus.
- `SVC-04` Nails: manicure/shape/color, controlled length extension/building, French, minimal, luxury/editorial, fantasy nail art, controlled bridal nails.
- `SVC-05` Men's Hair & Beard: haircut, fade, taper, men's color/gray, beard, moustache, line-up, hair+beard coordination, controlled groom styling.
- `CTRL-007` Chemical Smoothing / Keratin.
- `CTRL-009` Complex Bridal Full-Look coordination.

No new service IDs are created by this runtime. Skincare/facials/waxing and other services outside the frozen ontology remain `UNSUPPORTED / UNMAPPED` until formal ontology/change-control adds them.

## 3. Exact controlled-service routing

v0.4 explicitly resolves `CTRL-001…010` and their corresponding canonical service IDs where defined. Controlled routing adds the correct Knowledge/coordination owner and preserves professional-check requirements; it never creates execution permission or technical formulas.

Examples:

- `SVC-01-006 / CTRL-001` → Hair + Bridal coordination owner.
- `SVC-03-005 / CTRL-002` → Makeup + Bridal coordination owner.
- `SVC-04-007 / CTRL-003` → Nails + Bridal coordination owner.
- `SVC-05-009 / CTRL-004` → Men's Hair/Beard + event coordination owner.
- `SVC-02-009 / CTRL-005` → Hair Color / controlled correction.
- `SVC-01-007 / CTRL-006` → Extensions.
- `CTRL-007` → Smoothing/Keratin.
- `SVC-03-006 / CTRL-008` → Corrective/Coverage Makeup.
- `CTRL-009` → Complete Bridal coordination.
- `SVC-04-002 / CTRL-010` → Nail Length Extension/Building.

## 4. Professional Multi-View Evidence Manager

Capture is service-specific rather than globally hardcoded.

### Hair / Haircut
Required before ranked recommendation:
- FRONT
- LEFT_45
- RIGHT_45

Conditional when decision-material:
- LEFT_PROFILE
- RIGHT_PROFILE
- BACK
- TOP_CROWN

### Hair Color
Required:
- FRONT
- LEFT_45
- RIGHT_45
- BACK

Conditional:
- ROOT_DETAIL
- MID_LENGTH_DETAIL
- ENDS_DETAIL

### Makeup
Required:
- FRONT
- LEFT_45
- RIGHT_45

Conditional:
- EYE_DETAIL
- LIP_DETAIL

### Nails
Required:
- LEFT_HAND_TOP
- RIGHT_HAND_TOP

Conditional:
- LEFT_HAND_SIDE
- RIGHT_HAND_SIDE
- NAIL_DETAIL

### Men's Hair & Beard
Required:
- FRONT
- LEFT_45
- RIGHT_45

Conditional:
- LEFT_PROFILE
- RIGHT_PROFILE
- BACK
- TOP_CROWN

### Bridal / Complete Look
Required:
- FRONT
- LEFT_45
- RIGHT_45
- BACK
- LEFT_HAND_TOP
- RIGHT_HAND_TOP

Conditional component views are requested only when relevant.

### Extensions / Smoothing
Their own hair-focused front/45/back plus optional technical-detail views are used.

**Hard rule:** AG-03 may produce a partial analysis from an incomplete set, but AG-04 ranked Recommendation is not released until the active service's minimum professional view set is present. Conditional views remain adaptive and are requested only for material evidence gaps.

## 5. AG-03 — Cross-Domain Beauty Analysis

AG-03 receives multiple `CLIENT_IMAGE` views and explicit client/specialist context. It produces:

- image/view sufficiency;
- evidence buckets: `OBSERVED`, `USER_REPORTED`, `INFERRED`, `UNKNOWN`, `REQUIRES_PROFESSIONAL_CHECK`;
- domain-specific visible state;
- Source Reality locks;
- Shared Client Analysis;
- Specialist Analysis;
- Strategy Before Recommendation;
- limitations / minimum additional input.

Domain observations are bounded:

- Hair: visible length, texture/pattern direction, apparent density/volume, silhouette, growth direction, fringe/hairline/current style.
- Color: visible depth/lightness, warm/cool/neutral direction, contrast, visible gray/unevenness; never hidden chemical history from images.
- Makeup: visible styling geometry relevant to requested makeup domains; no skin diagnosis or facial-anatomy rewriting.
- Nails: visible length/shape/nail-bed/hand coordination; no diagnosis of disease.
- Beard: current visible coverage/distribution/length/moustache/line geometry; no biological growth potential inference.
- Combined Look: coordination over component analyses, not a new technical authority.

Multiple images improve visibility only. They do not reveal hidden history, health, ethnicity, personality or biological facts.

## 6. Analysis Before Recommendation — Hard Gate

v0.4 enforces:

```text
NO_RANKED_RECOMMENDATION_BEFORE_ANALYSIS_REVIEW
```

`run_analysis` stops at `ANALYSIS_REVIEW`. AG-04 remains `PENDING` with gate `ANALYSIS_REVIEW_REQUIRED`. Only explicit Shared/Specialist acknowledgment through `/ack-analysis` permits `run_recommendation`.

This prevents the product from behaving like a catalog that receives a photo and immediately emits style cards.

## 7. AG-04 — Custom Direction Composer

Recommendations are not restricted to famous model/style names. Named styles can be references, but the recommendation unit is a **decision direction / custom composition**.

Current component libraries:

- Hair components
- Color components
- Makeup components
- Nail components
- Beard components

AG-04 composes components using evidence, goal, desired change, maintenance, event/context, Safety and service ownership.

Core roles remain:

- `A — BEST FIT`
- `B — ALTERNATIVE`
- `C — BOLDER`

Optional valid `D/E/F — EXPLORE` may be added. No filler option is required when fewer valid directions exist.

Men's beard-specific source guards are an example of a general rule: a component that requires source evidence not present in the client must not enter ordinary ranking. The same principle applies to hair length, nail extension, color-only geometry and other domains.

## 8. AG-05 — Domain-Specific Preview Contracts

All previews share:

- `PRESERVE_IDENTITY`
- `PRESERVE_UNRELATED_REGIONS`
- `NO_UNSOLICITED_BEAUTIFICATION`
- source reality is authoritative
- provider output is untrusted until QA

Additional locks:

### Hair Color
`COLOR_ONLY_PRESERVE_CUT_LENGTH_SHAPE`

### Makeup
`PRESERVE_FACE_ANATOMY`
`EDIT_ONLY_REQUESTED_MAKEUP_DOMAINS`

### Nails
`PRESERVE_HAND_FINGER_GEOMETRY`
`PRESERVE_SKIN_JEWELRY_UNLESS_REQUESTED`

### Men's Hair / Beard
`NO_BEARD_COVERAGE_INCREASE`
`NO_HAIR_LENGTH_FABRICATION`

### Extensions
`EXTENSION_VISUALIZATION_NOT_FEASIBILITY_PROOF`

Complete looks apply only selected component changes; one component's success cannot hide another component's unresolved state.

## 9. Visual Integrity QA

Provider output is saved to Quarantine and is not published directly.

QA checks include:

- requested change visible;
- identity continuity;
- face/hand geometry drift as relevant;
- unrelated-region drift;
- Source Reality violations;
- color-only geometry preservation;
- makeup anatomy preservation;
- nail hand/finger preservation;
- beard coverage preservation.

Rejected output is deleted from the publish path and may trigger a bounded retry. If no attempt passes, ABC returns an honest limitation rather than a fake Preview success.

## 10. Model / Provider Runtime

Agent contracts remain semantic and provider-independent. Runtime may route:

- AG-02 Consultation → conversational/reasoning model;
- AG-03 Analysis → multimodal model;
- AG-04 Recommendation → reasoning/deterministic composition;
- AG-05 Preview → image-editing provider;
- AG-08 Safety → rules + model where appropriate;
- AG-10 Output → deterministic rendering + model where useful.

Model names are runtime configuration, not product truth. All salon editions inherit the same provider-routing and capability-truthfulness rules.

## 11. Current validation result

Locally validated in v0.4.0:

- Python compile;
- JavaScript syntax;
- legacy men's alias compatibility;
- all current core domain profiles;
- all controlled-route mapping examples;
- service-specific capture plans;
- partial multi-view analysis with recommendation blocking;
- hard Analysis Review gate;
- bounded Core Recommendation after acknowledgment;
- custom composition;
- sparse-beard source guard;
- domain-specific Preview locks;
- combined-look component coordination;
- Preview Quarantine → reject → retry → publish only PASS;
- offline E2E for Hair, Hair Color, Makeup, Nails, Men's Hair/Beard and Bridal Complete;
- no fake Preview success without provider credentials.

Not yet claimed:

- paid-provider Live multi-view validation for every service family;
- empirical visual-quality PASS across all domains;
- production-ready deterministic mask/full-frame-lock compositor;
- complete women/nails/makeup edition UI polish;
- Pilot Ready or Production Ready.
