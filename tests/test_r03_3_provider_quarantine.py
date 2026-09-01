from __future__ import annotations

import pytest

from abc_core.capabilities import CAPABILITIES, CapabilityState
from abc_core.state import (
    ActorContext,
    ActorType,
    AnalysisState,
    ClientSelection,
    InputAsset,
    RecommendationOption,
    RecommendationRole,
    RecommendationSet,
    RequestState,
    SalonSessionState,
    SessionMutationEngine,
)
from abc_core.tenancy import SalonConfig
from abc_core.visual_mask import (
    MaskAuthorization,
    MaskCandidate,
    MaskMode,
    MaskSpan,
    RegionMask,
    fingerprint_mask_candidate,
)
from abc_core.visual_provider import (
    ArtifactTrust,
    InMemoryRawOutputQuarantine,
    ProviderDispatchReason,
    ProviderDispatchStatus,
    ProviderQuarantineRuntime,
    ProviderRawResult,
    QuarantineDisposition,
    RawArtifactNotPublishable,
    SourcePayload,
)
from abc_core.visual_request import EditRegion, MediaConsentState, VisualInputQuality, VisualPreviewRequest


TENANT = "T-R033"
SESSION = "SESSION-R033"
SERVICE = "SVC-01-001"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-05", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-33", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-33", tenant_id=TENANT)


def capabilities_on() -> CapabilityState:
    return CapabilityState(external_visual_provider=True, deterministic_full_frame_lock_compositor=True)


def state() -> SalonSessionState:
    mutation = SessionMutationEngine()
    current = SalonSessionState(tenant_id=TENANT, session_id=SESSION)
    current = mutation.set_request(current, SYSTEM, RequestState(request_id="CORE-REQ", service_ids=(SERVICE,)))
    current = mutation.add_input_asset(current, CLIENT, InputAsset(asset_id="IMG-33", media_type="image/jpeg"))
    current = mutation.set_analysis(
        current,
        SPECIALIST,
        AnalysisState(analysis_id="AN-33", capture_sufficient=True, reviewed_by_specialist=True),
    )
    current = mutation.publish_recommendations(
        current,
        SYSTEM,
        RecommendationSet(
            recommendation_set_id="REC-33",
            core_options=(
                RecommendationOption(option_id="LOOK-A", title="Best Fit", role=RecommendationRole.BEST_FIT),
            ),
        ),
    )
    return mutation.select_option(current, CLIENT, ClientSelection(selection_id="SEL-33", option_id="LOOK-A"))


def config() -> SalonConfig:
    return SalonConfig(
        tenant_id=TENANT,
        salon_id="SALON-33",
        display_name="R03.3 Salon",
        enabled_service_ids=(SERVICE,),
        enabled_feature_ids=("VISUAL_PREVIEW",),
    )


def request() -> VisualPreviewRequest:
    return VisualPreviewRequest(
        request_id="VR-33",
        tenant_id=TENANT,
        session_id=SESSION,
        source_asset_id="IMG-33",
        option_id="LOOK-A",
        service_ids=(SERVICE,),
        requested_edit_regions=(EditRegion.HAIR,),
        source_media_consent=MediaConsentState.GRANTED,
        provider_processing_consent=MediaConsentState.GRANTED,
        input_quality=VisualInputQuality.STRONG,
    )


def authorization(vr: VisualPreviewRequest) -> MaskAuthorization:
    return MaskAuthorization(
        authorization_id="AUTH-33",
        request_id=vr.request_id,
        tenant_id=vr.tenant_id,
        session_id=vr.session_id,
        source_asset_id=vr.source_asset_id,
        option_id=vr.option_id,
        width=8,
        height=8,
        region_masks=(
            RegionMask(
                region=EditRegion.HAIR,
                spans=(MaskSpan(y=1, x_start=1, x_end=7), MaskSpan(y=2, x_start=1, x_end=7)),
            ),
        ),
    )


def candidate(vr: VisualPreviewRequest, *, escaping: bool = False) -> MaskCandidate:
    spans = (
        (MaskSpan(y=1, x_start=0, x_end=8),)
        if escaping
        else (MaskSpan(y=1, x_start=2, x_end=6), MaskSpan(y=2, x_start=2, x_end=6))
    )
    item = MaskCandidate(
        mask_id="MASK-33",
        request_id=vr.request_id,
        tenant_id=vr.tenant_id,
        session_id=vr.session_id,
        source_asset_id=vr.source_asset_id,
        option_id=vr.option_id,
        mode=MaskMode.AUTO,
        width=8,
        height=8,
        region_masks=(RegionMask(region=EditRegion.HAIR, spans=spans),),
        mask_sha256="0" * 64,
    )
    return item.model_copy(update={"mask_sha256": fingerprint_mask_candidate(item)})


class FakeAdapter:
    provider_id = "FAKE-VISUAL"

    def __init__(self, result: ProviderRawResult | None = None, *, fail: bool = False) -> None:
        self.calls = 0
        self.last_envelope = None
        self.last_mask = None
        self.fail = fail
        self.result = result or ProviderRawResult(
            provider_id=self.provider_id,
            provider_request_id="P-33",
            media_type="image/png",
            content=b"raw-provider-image",
        )

    def dispatch(self, envelope, *, source, mask):
        self.calls += 1
        self.last_envelope = envelope
        self.last_mask = mask
        if self.fail:
            raise RuntimeError("simulated provider failure")
        return self.result


def run(*, caps=None, mask=None, source=None, instruction="apply selected governed direction", adapter=None, quarantine=None):
    current = state()
    vr = request()
    q = quarantine if quarantine is not None else InMemoryRawOutputQuarantine()
    provider = adapter or FakeAdapter()
    runtime = ProviderQuarantineRuntime(capabilities=caps or capabilities_on(), quarantine=q)
    decision = runtime.dispatch(
        request=vr,
        state=current,
        salon_config=config(),
        allowed_edit_regions=(EditRegion.HAIR,),
        authorization=authorization(vr),
        candidate=mask or candidate(vr),
        source=source or SourcePayload(asset_id="IMG-33", media_type="image/jpeg", content=b"source-image"),
        instruction=instruction,
        adapter=provider,
    )
    return current, provider, q, decision


def test_valid_r03_1_and_r03_2_path_calls_adapter_once_and_quarantines_raw_output_only():
    current, provider, q, decision = run()
    assert decision.status is ProviderDispatchStatus.QUARANTINED
    assert decision.reasons == ()
    assert provider.calls == 1
    assert len(q) == 1
    artifact = decision.quarantine
    assert artifact is not None
    assert artifact.trust is ArtifactTrust.UNTRUSTED
    assert artifact.disposition is QuarantineDisposition.HOLD
    assert artifact.direct_preview_publishable is False
    assert artifact.payload == b"raw-provider-image"
    assert current.preview is None
    assert provider.last_envelope.mask_sha256 == provider.last_mask.mask_sha256


def test_quarantined_raw_artifact_can_never_self_promote_to_decision_preview():
    _, _, _, decision = run()
    with pytest.raises(RawArtifactNotPublishable):
        decision.quarantine.require_preview_publishable()


def test_current_global_capability_truth_blocks_before_provider_call():
    current = state()
    vr = request()
    provider = FakeAdapter()
    q = InMemoryRawOutputQuarantine()
    decision = ProviderQuarantineRuntime(capabilities=CAPABILITIES, quarantine=q).dispatch(
        request=vr,
        state=current,
        salon_config=config(),
        allowed_edit_regions=(EditRegion.HAIR,),
        authorization=authorization(vr),
        candidate=candidate(vr),
        source=SourcePayload(asset_id="IMG-33", media_type="image/jpeg", content=b"source-image"),
        instruction="governed edit",
        adapter=provider,
    )
    assert decision.status is ProviderDispatchStatus.BLOCKED
    assert ProviderDispatchReason.R03_1_PREFLIGHT_BLOCKED in decision.reasons
    assert ProviderDispatchReason.R03_2_MASK_BLOCKED in decision.reasons
    assert provider.calls == 0
    assert len(q) == 0


def test_mask_that_escapes_exact_r03_2_authorization_never_reaches_provider():
    vr = request()
    current, provider, q, decision = run(mask=candidate(vr, escaping=True))
    assert decision.status is ProviderDispatchStatus.BLOCKED
    assert decision.reasons == (ProviderDispatchReason.R03_2_MASK_BLOCKED,)
    assert provider.calls == 0
    assert len(q) == 0
    assert current.preview is None


def test_source_payload_must_bind_to_the_exact_canonical_source_asset():
    source = SourcePayload(asset_id="OTHER-IMG", media_type="image/jpeg", content=b"source-image")
    _, provider, q, decision = run(source=source)
    assert ProviderDispatchReason.SOURCE_ASSET_BINDING_MISMATCH in decision.reasons
    assert provider.calls == 0
    assert len(q) == 0


def test_source_media_type_must_match_canonical_asset_metadata():
    source = SourcePayload(asset_id="IMG-33", media_type="image/png", content=b"source-image")
    _, provider, _, decision = run(source=source)
    assert ProviderDispatchReason.SOURCE_MEDIA_TYPE_MISMATCH in decision.reasons
    assert provider.calls == 0


def test_blank_provider_instruction_is_fail_closed_before_dispatch():
    _, provider, _, decision = run(instruction="   ")
    assert decision.reasons == (ProviderDispatchReason.INSTRUCTION_EMPTY,)
    assert provider.calls == 0


def test_provider_exception_is_fail_closed_and_does_not_create_fake_artifact():
    provider = FakeAdapter(fail=True)
    _, _, q, decision = run(adapter=provider)
    assert decision.status is ProviderDispatchStatus.FAILED
    assert decision.reasons == (ProviderDispatchReason.PROVIDER_ERROR,)
    assert decision.quarantine is None
    assert provider.calls == 1
    assert len(q) == 0


def test_malformed_provider_output_is_still_quarantined_but_rejected_downstream():
    raw = ProviderRawResult(
        provider_id="WRONG-PROVIDER",
        provider_request_id="",
        media_type="text/plain",
        content=b"not-an-image",
    )
    _, provider, q, decision = run(adapter=FakeAdapter(result=raw))
    assert decision.status is ProviderDispatchStatus.QUARANTINED_REJECTED
    assert set(decision.reasons) == {
        ProviderDispatchReason.RAW_PROVIDER_ID_MISMATCH,
        ProviderDispatchReason.RAW_PROVIDER_REQUEST_ID_MISSING,
        ProviderDispatchReason.RAW_PROVIDER_MEDIA_NOT_IMAGE,
    }
    assert provider.calls == 1
    assert len(q) == 1
    assert decision.quarantine.disposition is QuarantineDisposition.REJECTED
    assert decision.quarantine.direct_preview_publishable is False


def test_empty_provider_payload_is_quarantined_rejected_not_published():
    raw = ProviderRawResult(
        provider_id="FAKE-VISUAL",
        provider_request_id="P-EMPTY",
        media_type="image/png",
        content=b"",
    )
    _, _, q, decision = run(adapter=FakeAdapter(result=raw))
    assert decision.status is ProviderDispatchStatus.QUARANTINED_REJECTED
    assert decision.reasons == (ProviderDispatchReason.RAW_PROVIDER_PAYLOAD_EMPTY,)
    assert len(q) == 1


def test_dispatch_fingerprint_and_quarantine_id_are_deterministic_for_same_bound_input():
    _, _, _, first = run()
    _, _, _, second = run()
    assert first.dispatch_fingerprint == second.dispatch_fingerprint
    assert first.quarantine.quarantine_id == second.quarantine.quarantine_id


def test_source_byte_change_changes_dispatch_fingerprint_even_for_same_asset_id():
    _, _, _, first = run(source=SourcePayload(asset_id="IMG-33", media_type="image/jpeg", content=b"source-A"))
    _, _, _, second = run(source=SourcePayload(asset_id="IMG-33", media_type="image/jpeg", content=b"source-B"))
    assert first.dispatch_fingerprint != second.dispatch_fingerprint


def test_r03_3_path_is_read_only_against_canonical_session_truth():
    current = state()
    before = current.canonical_snapshot()
    vr = request()
    provider = FakeAdapter()
    ProviderQuarantineRuntime(capabilities=capabilities_on()).dispatch(
        request=vr,
        state=current,
        salon_config=config(),
        allowed_edit_regions=(EditRegion.HAIR,),
        authorization=authorization(vr),
        candidate=candidate(vr),
        source=SourcePayload(asset_id="IMG-33", media_type="image/jpeg", content=b"source-image"),
        instruction="governed edit",
        adapter=provider,
    )
    assert current.canonical_snapshot() == before
