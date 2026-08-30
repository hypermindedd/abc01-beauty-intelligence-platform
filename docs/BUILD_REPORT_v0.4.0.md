# ABC CORE RUNTIME v0.4.0 — Build & Validation Report

## Result

`LOCAL_STRUCTURAL_AND_OFFLINE_E2E = PASS`

This release moves professional analysis / multi-view / recommendation / visual-integrity behavior into the shared ABC Core rather than a Men's Salon-specific branch.

## Implemented

- Cross-domain service-profile router over current frozen ontology.
- Exact controlled routing for `CTRL-001…010` and corresponding SVC mappings where defined.
- Service-specific Professional Multi-View Capture plans.
- Minimum professional view gate before ranked Recommendation.
- AG-03 multi-view analysis with Shared/Specialist briefs and Source Reality locks.
- Hard `ANALYSIS_REVIEW_REQUIRED` gate before AG-04.
- Custom Direction Composer for Hair, Color, Makeup, Nails, Men's Hair/Beard and Complete Look.
- Domain-specific Preview contracts.
- Provider-output Quarantine + QA + bounded retry/reject.
- Dynamic Cross-Domain demo surface for service selection and multi-view upload.
- HEIC/HEIF normalization on macOS via native `sips`.

## Local validation

- Python compile: PASS
- JavaScript syntax: PASS
- Legacy Men's v0.3 alias compatibility: PASS
- Cross-domain profile / controlled-route tests: PASS
- Professional Multi-View gate tests: PASS
- Analysis-before-Recommendation tests: PASS
- Custom-composition tests: PASS
- Preview lock tests: PASS
- Preview Quarantine/retry test: PASS
- Offline FastAPI E2E: PASS
- Upgrade installer preservation test (`.env.local` + `data/`): PASS

## E2E domains covered

- Hair
- Hair Color
- Makeup
- Nails
- Men's Hair & Beard
- Bridal / Complete Look

Extensions and Smoothing are covered structurally/profile-wise; their paid-provider live visual paths still require dedicated Real-Mac validation.

## No false PASS

The following are not claimed:

- Live paid-provider multi-view PASS across every ABC domain.
- Empirical visual-quality PASS across Hair/Color/Makeup/Nails/Bridal.
- Final deterministic mask/full-frame-lock production compositor.
- Pilot Ready.
- Production Ready.

## Scope boundary

The Core does not add services absent from the current frozen ontology. `skincare/facials`, waxing, medical scalp/hair-loss treatment, transplant and replacement systems remain unsupported until controlled ontology expansion.
