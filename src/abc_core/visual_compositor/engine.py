from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from abc_core.visual_mask import FrameLockPolicy, MaskCandidate, ValidatedMask
from abc_core.visual_provider import QuarantineDisposition, QuarantinedProviderArtifact

from .contracts import LockedCompositeArtifact, RasterFrame


class CompositeStatus(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class CompositeReason(StrEnum):
    QUARANTINE_NOT_HELD = "QUARANTINE_NOT_HELD"
    QUARANTINE_BINDING_MISMATCH = "QUARANTINE_BINDING_MISMATCH"
    VALIDATED_MASK_BINDING_MISMATCH = "VALIDATED_MASK_BINDING_MISMATCH"
    MASK_CANDIDATE_BINDING_MISMATCH = "MASK_CANDIDATE_BINDING_MISMATCH"
    MASK_DIGEST_MISMATCH = "MASK_DIGEST_MISMATCH"
    AUTHORIZATION_DIGEST_MISMATCH = "AUTHORIZATION_DIGEST_MISMATCH"
    SOURCE_PROVENANCE_MISMATCH = "SOURCE_PROVENANCE_MISMATCH"
    PROVIDER_PROVENANCE_MISMATCH = "PROVIDER_PROVENANCE_MISMATCH"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    LOCK_POLICY_MISMATCH = "LOCK_POLICY_MISMATCH"
    MASK_SPAN_OUT_OF_BOUNDS = "MASK_SPAN_OUT_OF_BOUNDS"
    LOCKED_PIXEL_VERIFICATION_FAILED = "LOCKED_PIXEL_VERIFICATION_FAILED"


@dataclass(frozen=True)
class CompositeDecision:
    status: CompositeStatus
    publish_downstream_allowed: bool
    reasons: tuple[CompositeReason, ...]
    artifact: LockedCompositeArtifact | None = None

    def require_downstream_artifact(self) -> LockedCompositeArtifact:
        if not self.publish_downstream_allowed or self.artifact is None:
            values = ", ".join(reason.value for reason in self.reasons)
            raise RuntimeError(f"R03.4 deterministic compositor blocked: {values}")
        return self.artifact


def _binding_from_mask(mask: ValidatedMask) -> tuple[object, ...]:
    return (
        mask.request_id,
        mask.tenant_id,
        mask.session_id,
        mask.source_asset_id,
        mask.option_id,
        mask.canonical_revision,
        mask.mask_id,
        mask.mask_sha256,
        mask.authorization_sha256,
    )


def _active_pixels(candidate: MaskCandidate) -> set[int]:
    active: set[int] = set()
    for region in candidate.region_masks:
        for span in region.spans:
            for x in range(span.x_start, span.x_end):
                active.add(span.y * candidate.width + x)
    return active


def _locked_verification_digest(source: RasterFrame, composite: bytes, active: set[int]) -> str:
    h = hashlib.sha256()
    channels = source.channels
    for pixel_index in range(source.width * source.height):
        if pixel_index in active:
            continue
        start = pixel_index * channels
        end = start + channels
        h.update(pixel_index.to_bytes(8, "big"))
        h.update(source.pixels[start:end])
        h.update(composite[start:end])
    return h.hexdigest()


@dataclass(frozen=True)
class DeterministicFullFrameLockCompositor:
    """R03.4 source-authoritative compositor plus locked-pixel verification.

    Provider pixels are copied only for pixels active in the exact R03.2 mask.
    Every other pixel is copied from the decoded source frame. The result is then
    independently verified against the source outside the mask before it may move
    to downstream Visual QA. This component never creates a Decision Preview.
    """

    def compose(
        self,
        *,
        quarantine: QuarantinedProviderArtifact,
        validated_mask: ValidatedMask,
        mask_candidate: MaskCandidate,
        source: RasterFrame,
        provider: RasterFrame,
    ) -> CompositeDecision:
        reasons: list[CompositeReason] = []

        if quarantine.disposition is not QuarantineDisposition.HOLD:
            reasons.append(CompositeReason.QUARANTINE_NOT_HELD)

        quarantine_binding = (
            quarantine.request_id,
            quarantine.tenant_id,
            quarantine.session_id,
            quarantine.source_asset_id,
            quarantine.option_id,
            quarantine.canonical_revision,
            quarantine.mask_id,
            quarantine.mask_sha256,
            quarantine.authorization_sha256,
        )
        if quarantine_binding != _binding_from_mask(validated_mask):
            reasons.append(CompositeReason.QUARANTINE_BINDING_MISMATCH)

        candidate_binding = (
            mask_candidate.request_id,
            mask_candidate.tenant_id,
            mask_candidate.session_id,
            mask_candidate.source_asset_id,
            mask_candidate.option_id,
            mask_candidate.mask_id,
            mask_candidate.mask_sha256,
        )
        expected_candidate_binding = (
            validated_mask.request_id,
            validated_mask.tenant_id,
            validated_mask.session_id,
            validated_mask.source_asset_id,
            validated_mask.option_id,
            validated_mask.mask_id,
            validated_mask.mask_sha256,
        )
        if candidate_binding != expected_candidate_binding:
            reasons.append(CompositeReason.MASK_CANDIDATE_BINDING_MISMATCH)

        if quarantine.mask_sha256 != validated_mask.mask_sha256:
            reasons.append(CompositeReason.MASK_DIGEST_MISMATCH)
        if quarantine.authorization_sha256 != validated_mask.authorization_sha256:
            reasons.append(CompositeReason.AUTHORIZATION_DIGEST_MISMATCH)
        if source.provenance_sha256 != quarantine.source_sha256:
            reasons.append(CompositeReason.SOURCE_PROVENANCE_MISMATCH)
        if provider.provenance_sha256 != quarantine.raw_sha256:
            reasons.append(CompositeReason.PROVIDER_PROVENANCE_MISMATCH)

        expected_dimensions = (validated_mask.width, validated_mask.height)
        if (source.width, source.height) != expected_dimensions or (
            provider.width,
            provider.height,
        ) != expected_dimensions or (mask_candidate.width, mask_candidate.height) != expected_dimensions:
            reasons.append(CompositeReason.DIMENSION_MISMATCH)
        if source.channels != provider.channels:
            reasons.append(CompositeReason.CHANNEL_MISMATCH)
        if validated_mask.lock_policy is not FrameLockPolicy.FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION:
            reasons.append(CompositeReason.LOCK_POLICY_MISMATCH)

        span_out_of_bounds = any(
            span.y >= validated_mask.height or span.x_end > validated_mask.width
            for region in mask_candidate.region_masks
            for span in region.spans
        )
        if span_out_of_bounds:
            reasons.append(CompositeReason.MASK_SPAN_OUT_OF_BOUNDS)

        unique = tuple(dict.fromkeys(reasons))
        if unique:
            return CompositeDecision(CompositeStatus.BLOCKED, False, unique)

        active = _active_pixels(mask_candidate)
        channels = source.channels
        composite = bytearray(source.pixels)
        for pixel_index in active:
            start = pixel_index * channels
            end = start + channels
            composite[start:end] = provider.pixels[start:end]

        # Independent locked-pixel verification; a future optimized compositor must
        # continue to satisfy this invariant even if the construction changes.
        verification_failed = False
        for pixel_index in range(source.width * source.height):
            if pixel_index in active:
                continue
            start = pixel_index * channels
            end = start + channels
            if composite[start:end] != source.pixels[start:end]:
                verification_failed = True
                break
        if verification_failed:
            return CompositeDecision(
                CompositeStatus.BLOCKED,
                False,
                (CompositeReason.LOCKED_PIXEL_VERIFICATION_FAILED,),
            )

        composite_bytes = bytes(composite)
        verification_sha = _locked_verification_digest(source, composite_bytes, active)
        artifact = LockedCompositeArtifact(
            composite_id=f"cmp-{quarantine.quarantine_id}",
            quarantine_id=quarantine.quarantine_id,
            dispatch_id=quarantine.dispatch_id,
            request_id=validated_mask.request_id,
            tenant_id=validated_mask.tenant_id,
            session_id=validated_mask.session_id,
            source_asset_id=validated_mask.source_asset_id,
            option_id=validated_mask.option_id,
            canonical_revision=validated_mask.canonical_revision,
            mask_id=validated_mask.mask_id,
            mask_sha256=validated_mask.mask_sha256,
            authorization_sha256=validated_mask.authorization_sha256,
            source_sha256=quarantine.source_sha256,
            raw_sha256=quarantine.raw_sha256,
            width=source.width,
            height=source.height,
            channels=channels,
            composite_pixel_sha256=hashlib.sha256(composite_bytes).hexdigest(),
            locked_pixel_verification_sha256=verification_sha,
            edited_pixel_count=len(active),
            locked_pixel_count=source.width * source.height - len(active),
            pixels=composite_bytes,
        )
        return CompositeDecision(CompositeStatus.PASS, True, (), artifact)
