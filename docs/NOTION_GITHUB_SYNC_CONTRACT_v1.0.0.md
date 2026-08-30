# ABC.01 | Notion ↔ GitHub Sync Contract v1.0.0

## GitHub owns
- source code
- tests
- manifests used by runtime/build
- CI configuration
- commit history
- release/tag history

## Notion owns management/governance mirror
- Project OS
- architecture decision records
- roadmap/waves
- evidence index
- gate status
- authority/change records
- current blocker and next valid action

## Never duplicate authority silently
Notion must not become a second editable source-code tree. GitHub must not replace explicit HUMAN decisions or approved Productization authority records.

## Reconciliation rule
Every meaningful GitHub state change that changes the project management state must be reconciled into Notion with:
- exact commit/tag
- evidence hash or CI result
- resulting State Version
- actor attribution
- next action
