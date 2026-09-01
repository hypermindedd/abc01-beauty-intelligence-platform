from __future__ import annotations

import hashlib

import pytest

from abc_core.visual_compositor import (
    CompositeReason,
    CompositeStatus,
    DeterministicFullFrameLockCompositor,
    RasterFrame,
)
from abc_core.visual_mask import (
    FrameLockPolicy,
    MaskCandidate,
    MaskMode,
    MaskSpan,
    RegionMask,
    ValidatedMask,
    fingerprint_mask_candidate,
)
from abc_core.visual_provider import (
    ArtifactTrust,
    QuarantineDisposition,
    QuarantinedProviderArtifact,
)
from abc_core.visual_request import EditRegion


REQ = "REQ-34"
TENANT = "TENANT-34"
SESSION = "SESSION-34"
SOURCE = "ASSET-34"
OPTION = "LOOK-A"
MASK_ID = "MASK-34"
AUTH_SHA = "a" * 64
SOURCE_SHA = "b" * 64
RAW_SHA = "c" * 64


def candidate() -> MaskCandidate:
    provisional = MaskCandidate(
        mask_id=MASK_ID,
        request_id=REQ,
        tenant_id=TENANT,
        session_id=SESSION,
        source_asset_id=SOURCE,
        option_id=OPTION,
        mode=MaskMode.AUTO,
        width=3,
        height=2,
        region_masks=(
            RegionMask(
                region=EditRegion.HAIR,
                spans=(MaskSpan(y=0, x_start=1, x_end=3), MaskSpan(y=1, x_start=2, x_end=3)),
            ),
        ),
        mask_sha256="0" * 64,
    )
    return provisional.model_copy(update={"mask_sha256": fingerprint_mask_candidate(provisional)})


def validated(mask: MaskCandidate) -> ValidatedMask:
    return ValidatedMask(
        mask_id=mask.mask_id,
        authorization_id="AUTH-34",
        request_id=REQ,
        tenant_id=TENANT,
        session_id=SESSION,
        source_asset_id=SOURCE,
        option_id=OPTION,
        canonical_revision=7,
        width=3,
        height=2,
        regions=(EditRegion.HAIR.value,),
        mask_sha256=mask.mask_sha256,
        authorization_sha256=AUTH_SHA,
        lock_policy=FrameLockPolicy.FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION,
    )


def quarantine(mask: MaskCandidate, **overrides) -> QuarantinedProviderArtifact:
    payload = dict(
        quarantine_id="Q-34",
        dispatch_id="D-34",
        dispatch_fingerprint="d" * 64,
        request_id=REQ,
        tenant_id=TENANT,
        session_id=SESSION,
        source_asset_id=SOURCE,
        option_id=OPTION,
        canonical_revision=7,
        provider_adapter_id="test-adapter",
        provider_claimed_id="test-provider",
        provider_request_id="P-34",
        mask_id=mask.mask_id,
        mask_sha256=mask.mask_sha256,
        authorization_sha256=AUTH_SHA,
        source_sha256=SOURCE_SHA,
        raw_sha256=RAW_SHA,
        media_type="image/png",
        byte_length=123,
        disposition=QuarantineDisposition.HOLD,
        rejection_reasons=(),
        trust=ArtifactTrust.UNTRUSTED,
        direct_preview_publishable=False,
        payload=b"raw-provider-image",
    )
    payload.update(overrides)
    return QuarantinedProviderArtifact(**payload)


def frames():
    # 3x2 RGB. Every source pixel is distinct. Provider is deliberately very different.
    source_pixels = bytes(range(18))
    provider_pixels = bytes(200 + i for i in range(18))
    return (
        RasterFrame(3, 2, 3, source_pixels, SOURCE_SHA),
        RasterFrame(3, 2, 3, provider_pixels, RAW_SHA),
    )


def test_compositor_uses_provider_only_inside_exact_mask_and_source_everywhere_else():
    mask = candidate()
    source, provider = frames()
    result = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask),
        validated_mask=validated(mask),
        mask_candidate=mask,
        source=source,
        provider=provider,
    )
    assert result.status is CompositeStatus.PASS
    artifact = result.require_downstream_artifact()
    active = {1, 2, 5}
    for pixel in range(6):
        sl = slice(pixel * 3, pixel * 3 + 3)
        expected = provider.pixels[sl] if pixel in active else source.pixels[sl]
        assert artifact.pixels[sl] == expected
    assert artifact.edited_pixel_count == 3
    assert artifact.locked_pixel_count == 3
    assert artifact.composite_pixel_sha256 == hashlib.sha256(artifact.pixels).hexdigest()
    assert artifact.direct_preview_publishable is False


def test_locked_composite_cannot_claim_direct_preview_publishability():
    mask = candidate()
    source, provider = frames()
    artifact = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask),
        validated_mask=validated(mask),
        mask_candidate=mask,
        source=source,
        provider=provider,
    ).require_downstream_artifact()
    with pytest.raises(RuntimeError, match="downstream Visual QA"):
        artifact.require_preview_publishable()


@pytest.mark.parametrize(
    ("q_overrides", "source_sha", "provider_sha", "reason"),
    [
        ({"disposition": QuarantineDisposition.REJECTED}, SOURCE_SHA, RAW_SHA, CompositeReason.QUARANTINE_NOT_HELD),
        ({"canonical_revision": 8}, SOURCE_SHA, RAW_SHA, CompositeReason.QUARANTINE_BINDING_MISMATCH),
        ({"authorization_sha256": "e" * 64}, SOURCE_SHA, RAW_SHA, CompositeReason.QUARANTINE_BINDING_MISMATCH),
        ({}, "f" * 64, RAW_SHA, CompositeReason.SOURCE_PROVENANCE_MISMATCH),
        ({}, SOURCE_SHA, "f" * 64, CompositeReason.PROVIDER_PROVENANCE_MISMATCH),
    ],
)
def test_fail_closed_for_untrusted_or_mismatched_integrity_inputs(q_overrides, source_sha, provider_sha, reason):
    mask = candidate()
    source, provider = frames()
    source = RasterFrame(source.width, source.height, source.channels, source.pixels, source_sha)
    provider = RasterFrame(provider.width, provider.height, provider.channels, provider.pixels, provider_sha)
    result = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask, **q_overrides),
        validated_mask=validated(mask),
        mask_candidate=mask,
        source=source,
        provider=provider,
    )
    assert result.status is CompositeStatus.BLOCKED
    assert result.publish_downstream_allowed is False
    assert reason in result.reasons


def test_stale_or_different_mask_candidate_cannot_be_substituted():
    mask = candidate()
    source, provider = frames()
    other = mask.model_copy(update={"option_id": "LOOK-B"})
    result = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask),
        validated_mask=validated(mask),
        mask_candidate=other,
        source=source,
        provider=provider,
    )
    assert CompositeReason.MASK_CANDIDATE_BINDING_MISMATCH in result.reasons


def test_dimension_mismatch_is_rejected_before_copying_pixels():
    mask = candidate()
    source, provider = frames()
    provider = RasterFrame(2, 3, 3, provider.pixels, RAW_SHA)
    result = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask),
        validated_mask=validated(mask),
        mask_candidate=mask,
        source=source,
        provider=provider,
    )
    assert CompositeReason.DIMENSION_MISMATCH in result.reasons


def test_channel_mismatch_is_rejected():
    mask = candidate()
    source, _ = frames()
    rgba = RasterFrame(3, 2, 4, bytes(range(24)), RAW_SHA)
    result = DeterministicFullFrameLockCompositor().compose(
        quarantine=quarantine(mask),
        validated_mask=validated(mask),
        mask_candidate=mask,
        source=source,
        provider=rgba,
    )
    assert CompositeReason.CHANNEL_MISMATCH in result.reasons


def test_raster_contract_rejects_wrong_byte_count_and_bad_provenance_digest():
    with pytest.raises(ValueError, match="byte length"):
        RasterFrame(2, 2, 3, b"too-short", SOURCE_SHA)
    with pytest.raises(ValueError, match="64-character"):
        RasterFrame(1, 1, 3, b"abc", "bad")
