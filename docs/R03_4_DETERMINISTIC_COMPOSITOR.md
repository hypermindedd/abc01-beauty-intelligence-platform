# ABC.01 R03.4 — Deterministic Full-Frame Lock Compositor & Locked-Pixel Verification

Status: engineering implementation candidate. This stage does not claim live visual, runtime-product, pilot or production readiness.

## Objective

R03.4 converts an R03.3 quarantined raw provider artifact into a deterministic composite while enforcing the canonical frame-lock policy:

`FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION`

The provider is authoritative nowhere outside the exact R03.2 validated mask. Locked pixels are copied from the decoded source frame, not from provider output.

## Required upstream authority

The compositor accepts only:

1. an R03.3 `QuarantinedProviderArtifact` in `HOLD` disposition;
2. the exact R03.2 `ValidatedMask` bound to that quarantine artifact;
3. the exact corresponding `MaskCandidate` geometry;
4. a decoded source raster whose provenance SHA-256 equals the governed source artifact SHA-256;
5. a decoded provider raster whose provenance SHA-256 equals the quarantined raw provider SHA-256.

The decoder/codec layer is outside R03.4 and must preserve/prove upstream artifact provenance. R03.4 does not claim a production codec or durable media store.

## Deterministic composition rule

For every pixel `p`:

- if `p` is active in the exact validated authorized mask, copy provider pixel bytes;
- otherwise copy source pixel bytes.

No blending, dilation, feathering or model-driven expansion of the authorized scope occurs in this Core compositor contract. Such processing would require separately governed authorization semantics.

## Locked-pixel verification

After construction, every pixel outside the authorized mask is independently compared byte-for-byte against the source raster. Any mismatch fails closed.

A deterministic verification digest binds pixel index + source locked bytes + composite locked bytes for every locked pixel.

## Fail-closed conditions

- rejected quarantine artifact;
- quarantine / validated-mask binding mismatch;
- substituted or stale mask candidate;
- mask or authorization digest mismatch;
- source or provider provenance mismatch;
- dimension mismatch;
- channel mismatch;
- wrong lock policy;
- mask span outside frame bounds;
- any locked-pixel verification failure.

## Publication boundary

`LockedCompositeArtifact` is an integrity artifact, not a `DecisionPreview`.

Even after R03.4 PASS:

`LOCKED COMPOSITE → DOWNSTREAM VISUAL QA → RETRY/REJECT/PASS → DECISION PREVIEW`

Direct Preview publication remains prohibited.

## Non-claims

- automatic segmentation: NO
- real external provider execution validated: NO
- production image codec/media persistence: NO
- identity/source-reality Visual QA: NO
- live cross-domain visual validation: NO
- Runtime Product PASS: NO
- Pilot Ready: NO
- Production Ready: NO
