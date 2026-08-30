# ABC.01 | GitHub Repository Bootstrap Contract v1.0.0

## Repository identity
Preferred private repository: `hypermindedd/abc01-beauty-intelligence-platform`

## Authority role
GitHub is the source of truth for source code and immutable code/build history once the dedicated remote exists. GitHub does not replace explicit HUMAN approval or the frozen Productization authority baseline.

## Initial imported engineering baseline
`ABC CORE RUNTIME v0.4.0 — CROSS-DOMAIN ENGINEERING BASELINE`

Status:
- local structural/offline validation: PASS
- live cross-domain validation: pending
- pilot ready: NO
- production ready: NO

## Required branches
- `main` — protected integration line after initial bootstrap
- feature/review branches for material changes

## Initial tag
`abc-core-runtime-v0.4.0-engineering-baseline`

The tag must not be described as production, pilot, canonical runtime PASS, or release approval.

## Repository layout
```text
.github/workflows/
server/
server/providers/
static/
tests/
docs/
manifests/
data/media/.gitkeep
data/sessions/.gitkeep
.env.example
.gitignore
README_FA.md
VERSION
SECURITY.md
CONTRIBUTING.md
requirements.txt
```

## Secrets boundary
Forbidden from Git:
- `.env.local`
- `OPENAI_API_KEY`
- provider secrets
- real client media
- private session data
- salon credentials

## Governance linkage
After the first remote commit:
1. record commit SHA and tag in ABC.01 Notion Project OS;
2. update Universal Project Registry state using optimistic concurrency;
3. append a Universal Project Event Log entry;
4. index validation evidence and hashes in ABC.01 Evidence & Gates.
