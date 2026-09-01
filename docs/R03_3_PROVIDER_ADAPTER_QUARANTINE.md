# ABC.01 R03.3 — Provider Adapter / Raw Output Quarantine

Status: engineering implementation candidate. This stage introduces the provider-neutral dispatch boundary and mandatory raw-output quarantine after the closed R03.1 and R03.2 integrity gates. It does not implement a production provider integration, deterministic compositor, locked-pixel verification, final Visual QA, or publish a Decision Preview.

## Objective

R03.3 ensures that no external visual-provider call can occur unless the current request passes the R03.1 pre-provider gate and the exact mask candidate passes the R03.2 pixel-scope validation at the same canonical session revision. Any provider result is untrusted by construction and must enter quarantine before any downstream compositor or QA path.

## Canonical sequence

`R03.1 Visual Request Gate → R03.2 Exact Mask Validation → R03.3 Provider Dispatch Envelope → Provider Adapter → Raw Output Quarantine`

Raw provider output must never become a Decision Preview directly.

## Provider-independent dispatch contract

The runtime creates an immutable `ProviderDispatchEnvelope` only after all pre-dispatch checks pass. The envelope binds:

- provider adapter ID;
- request / tenant / session;
- source asset ID and media type;
- exact source-content SHA-256;
- selected option and service scope;
- requested semantic edit regions;
- canonical Core revision;
- R03.2 validated mask ID and mask SHA-256;
- exact authorization SHA-256;
- mask frame dimensions;
- `FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION`;
- instruction SHA-256.

A deterministic dispatch fingerprint is derived from these governed values. This makes a provider call contextual to one exact request, source byte stream, selected direction, mask, authorization and Core revision.

## Source payload boundary

R03.3 receives source-image bytes from the media layer as an ephemeral `SourcePayload`. The asset ID and media type must match the canonical session input asset before the adapter can be called. The content digest is included in the dispatch fingerprint so replacing the bytes under the same asset ID changes dispatch identity.

## Provider adapter contract

`VisualProviderAdapter` is a provider-neutral protocol. R03.3 does not make any provider model a source of product truth. A future OpenAI or other provider implementation must satisfy the same governed envelope and cannot bypass R03.1 or R03.2.

This stage does not add or validate a real paid provider adapter. Tests inject a deterministic fake adapter only to validate the boundary behavior.

## Mandatory raw-output quarantine

Every successful adapter return becomes a `QuarantinedProviderArtifact` with:

- `trust = UNTRUSTED`;
- dispatch fingerprint and dispatch ID;
- request / tenant / session / source / option binding;
- provider adapter ID and provider-reported ID;
- provider request ID;
- mask and authorization hashes;
- source-content hash;
- raw-output SHA-256 and byte length;
- media type;
- quarantine disposition;
- `direct_preview_publishable = false`.

The artifact exposes no self-promotion route: attempting to require it as directly publishable raises `RawArtifactNotPublishable`.

## Malformed provider results

Provider output is not trusted merely because a provider call returned. Provider-ID mismatch, missing provider request ID, non-image media type or empty output are fail-closed downstream conditions. Such results are still retained in quarantine as `REJECTED` engineering evidence; they are never silently converted into a successful Preview.

A provider exception returns a failed dispatch decision and creates no fabricated provider artifact or Preview.

## Quarantine persistence truth

The R03.3 reference quarantine is `InMemoryRawOutputQuarantine` and explicitly reports `durable = false`. This is an engineering proof of the trust boundary, not a production media store, retention system, database or persistence capability.

## Canonical truth protection

R03.3 is read-only against `SalonSessionState`. Provider dispatch and quarantine creation do not mutate canonical session truth. A quarantined raw image is outside the canonical Preview state until later compositor, locked-pixel verification and Visual QA gates explicitly promote a verified artifact.

## Current capability truth

The repository-wide default capability state remains fail-closed:

- external visual provider: unavailable;
- deterministic full-frame lock compositor: unavailable;
- live cross-domain visual validation: unavailable;
- Pilot Ready: NO;
- Production Ready: NO.

Tests may inject temporary capability truth to exercise the provider boundary; this does not change runtime readiness claims.

## Current non-claims

- real OpenAI/provider adapter implemented and validated: NO
- automatic mask segmentation: NO
- production media persistence: NO
- deterministic full-frame compositor implemented/validated: NO
- locked-pixel verification implemented/validated: NO
- identity/source-reality final Visual QA validated: NO
- raw provider output directly publishable: NO
- live cross-domain visual validation: NO
- Runtime Product PASS: NO
- Pilot Ready: NO
- Production Ready: NO

## Next valid stage after PASS

R03.4 should implement the deterministic full-frame lock compositor and locked-pixel verification boundary. Only a non-rejected R03.3 quarantine artifact with valid dispatch provenance may enter that path; the compositor must restore all pixels outside the R03.2 validated authorized edit region from the source frame and prove the locked region remained exact before Visual QA can proceed.
