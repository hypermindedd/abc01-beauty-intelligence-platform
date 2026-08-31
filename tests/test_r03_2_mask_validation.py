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
    SafetyFlag,
    SafetyTier,
    SalonSessionState,
    SessionMutationEngine,
)
from abc_core.tenancy import SalonConfig
from abc_core.visual_mask import (
    FrameLockPolicy,
    MaskAuthorization,
    MaskCandidate,
    MaskMode,
    MaskSpan,
    MaskValidationGate,
    MaskValidationReason,
    MaskValidationRejected,
    MaskValidationStatus,
    RegionMask,
    fingerprint_mask_candidate,
)
from abc_core.visual_request import (
    EditRegion,
    MediaConsentState,
    VisualInputQuality,
    VisualPreviewRequest,
    VisualRequestGate,
)


TENANT = "T-R032"
SESSION = "SESSION-R032"
SERVICE = "SVC-01-001"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-05", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-32", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-32", tenant_id=TENANT)


def capabilities_on() -> CapabilityState:
    return CapabilityState(
        external_visual_provider=True,
        deterministic_full_frame_lock_compositor=True,
    )


def state() -> SalonSessionState:
    mutation = SessionMutationEngine()
    current = SalonSessionState(tenant_id=TENANT, session_id=SESSION)
    current = mutation.set_request(
        current,
        SYSTEM,
        RequestState(request_id="CORE-REQ", service_ids=(SERVICE,)),
    )
    current = mutation.add_input_asset(
        current,
        CLIENT,
        InputAsset(asset_id="IMG-32", media_type="image/jpeg"),
    )
    current = mutation.set_analysis(
        current,
        SPECIALIST,
        AnalysisState(analysis_id="AN-32", capture_sufficient=True, reviewed_by_specialist=True),
    )
    current = mutation.publish_recommendations(
        current,
        SYSTEM,
        RecommendationSet(
            recommendation_set_id="REC-32",
            core_options=(
                RecommendationOption(
                    option_id="LOOK-A",
                    title="Best Fit",
                    role=RecommendationRole.BEST_FIT,
                ),
            ),
        ),
    )
    return mutation.select_option(
        current,
        CLIENT,
        ClientSelection(selection_id="SEL-32", option_id="LOOK-A"),
    )


def config() -> SalonConfig:
    return SalonConfig(
        tenant_id=TENANT,
        salon_id="SALON-32",
        display_name="R03.2 Salon",
        enabled_service_ids=(SERVICE,),
        enabled_feature_ids=("VISUAL_PREVIEW",),
    )


def request(*, request_id: str = "VR-32", regions=(EditRegion.HAIR,)) -> VisualPreviewRequest:
    return VisualPreviewRequest(
        request_id=request_id,
        tenant_id=TENANT,
        session_id=SESSION,
        source_asset_id="IMG-32",
        option_id="LOOK-A",
        service_ids=(SERVICE,),
        requested_edit_regions=regions,
        source_media_consent=MediaConsentState.GRANTED,
        provider_processing_consent=MediaConsentState.GRANTED,
        input_quality=VisualInputQuality.STRONG,
    )


def preflight(current: SalonSessionState, visual_request: VisualPreviewRequest, *, caps=None):
    return VisualRequestGate(capabilities=caps or capabilities_on()).evaluate(
        request=visual_request,
        state=current,
        salon_config=config(),
        allowed_edit_regions=visual_request.requested_edit_regions,
    )


def hair_auth(visual_request: VisualPreviewRequest, *, width: int = 8, height: int = 8, regions=None):
    region_masks = regions or (
        RegionMask(
            region=EditRegion.HAIR,
            spans=(
                MaskSpan(y=1, x_start=1, x_end=7),
                MaskSpan(y=2, x_start=1, x_end=7),
                MaskSpan(y=3, x_start=2, x_end=6),
            ),
        ),
    )
    return MaskAuthorization(
        authorization_id="AUTH-32",
        request_id=visual_request.request_id,
        tenant_id=visual_request.tenant_id,
        session_id=visual_request.session_id,
        source_asset_id=visual_request.source_asset_id,
        option_id=visual_request.option_id,
        width=width,
        height=height,
        region_masks=region_masks,
    )


def candidate(
    visual_request: VisualPreviewRequest,
    *,
    width: int = 8,
    height: int = 8,
    regions=None,
    mode: MaskMode = MaskMode.AUTO,
    specialist_actor_id: str | None = None,
    source_asset_id: str | None = None,
):
    region_masks = regions or (
        RegionMask(
            region=EditRegion.HAIR,
            spans=(
                MaskSpan(y=1, x_start=2, x_end=6),
                MaskSpan(y=2, x_start=2, x_end=6),
            ),
        ),
    )
    item = MaskCandidate(
        mask_id="MASK-32",
        request_id=visual_request.request_id,
        tenant_id=visual_request.tenant_id,
        session_id=visual_request.session_id,
        source_asset_id=source_asset_id or visual_request.source_asset_id,
        option_id=visual_request.option_id,
        mode=mode,
        width=width,
        height=height,
        region_masks=region_masks,
        mask_sha256="0" * 64,
        specialist_actor_id=specialist_actor_id,
    )
    return item.model_copy(update={"mask_sha256": fingerprint_mask_candidate(item)})


def evaluate(current=None, visual_request=None, authorization=None, mask_candidate=None, *, caps=None):
    current = current or state()
    visual_request = visual_request or request()
    authorization = authorization or hair_auth(visual_request)
    mask_candidate = mask_candidate or candidate(visual_request)
    decision = preflight(current, visual_request, caps=caps)
    return MaskValidationGate().evaluate(
        preflight=decision,
        request=visual_request,
        state=current,
        authorization=authorization,
        candidate=mask_candidate,
    )


def test_valid_mask_becomes_the_only_r03_2_provider_dispatch_authorization_and_state_is_unchanged():
    current = state()
    before = current.canonical_snapshot()
    decision = evaluate(current=current)
    assert decision.status is MaskValidationStatus.PASS
    assert decision.provider_dispatch_allowed is True
    validated = decision.require_provider_dispatchable()
    assert validated.lock_policy is FrameLockPolicy.FULL_FRAME_LOCK_EXCEPT_VALIDATED_AUTHORIZED_EDIT_REGION
    assert validated.regions == ("HAIR",)
    assert current.canonical_snapshot() == before


def test_current_global_capability_truth_cannot_be_bypassed_by_a_valid_mask():
    decision = evaluate(caps=CAPABILITIES)
    assert decision.status is MaskValidationStatus.BLOCKED
    assert decision.reasons == (MaskValidationReason.R03_1_PREFLIGHT_BLOCKED,)


def test_r03_1_decision_is_cryptographically_contextual_not_reusable_for_another_request_binding():
    current = state()
    original = request(request_id="VR-ORIGINAL")
    original_preflight = preflight(current, original)
    changed = request(request_id="VR-CHANGED")
    decision = MaskValidationGate().evaluate(
        preflight=original_preflight,
        request=changed,
        state=current,
        authorization=hair_auth(changed),
        candidate=candidate(changed),
    )
    assert decision.reasons == (MaskValidationReason.R03_1_PREFLIGHT_BINDING_MISMATCH,)


def test_any_core_mutation_after_preflight_makes_mask_authorization_stale():
    current = state()
    visual_request = request()
    decision = preflight(current, visual_request)
    changed = SessionMutationEngine().add_safety_flag(
        current,
        SYSTEM,
        SafetyFlag(flag_id="S1-AFTER", tier=SafetyTier.S1, reason="later attention"),
    )
    result = MaskValidationGate().evaluate(
        preflight=decision,
        request=visual_request,
        state=changed,
        authorization=hair_auth(visual_request),
        candidate=candidate(visual_request),
    )
    assert result.reasons == (MaskValidationReason.STALE_CANONICAL_REVISION,)


def test_authorization_and_candidate_must_bind_to_exact_request_source_and_option():
    visual_request = request()
    bad_candidate = candidate(visual_request, source_asset_id="OTHER-IMG")
    result = evaluate(visual_request=visual_request, mask_candidate=bad_candidate)
    assert result.reasons == (MaskValidationReason.CANDIDATE_BINDING_MISMATCH,)

    auth = hair_auth(visual_request).model_copy(update={"source_asset_id": "OTHER-IMG"})
    result = evaluate(visual_request=visual_request, authorization=auth)
    assert result.reasons == (MaskValidationReason.AUTHORIZATION_BINDING_MISMATCH,)


def test_mask_dimensions_must_match_the_authorized_source_frame():
    visual_request = request()
    result = evaluate(
        visual_request=visual_request,
        authorization=hair_auth(visual_request, width=8, height=8),
        mask_candidate=candidate(visual_request, width=9, height=8),
    )
    assert MaskValidationReason.DIMENSION_MISMATCH in result.reasons


def test_authorization_and_candidate_region_sets_must_exactly_match_requested_regions():
    visual_request = request(regions=(EditRegion.HAIR, EditRegion.HAIR_COLOR))
    hair = RegionMask(region=EditRegion.HAIR, spans=(MaskSpan(y=1, x_start=1, x_end=4),))
    color = RegionMask(region=EditRegion.HAIR_COLOR, spans=(MaskSpan(y=2, x_start=1, x_end=4),))

    auth_missing = hair_auth(visual_request, regions=(hair,))
    candidate_both = candidate(visual_request, regions=(hair, color))
    first = evaluate(visual_request=visual_request, authorization=auth_missing, mask_candidate=candidate_both)
    assert MaskValidationReason.AUTHORIZATION_REGION_SCOPE_MISMATCH in first.reasons

    auth_both = hair_auth(visual_request, regions=(hair, color))
    candidate_missing = candidate(visual_request, regions=(hair,))
    second = evaluate(visual_request=visual_request, authorization=auth_both, mask_candidate=candidate_missing)
    assert MaskValidationReason.CANDIDATE_REGION_SCOPE_MISMATCH in second.reasons


def test_mask_spans_cannot_escape_frame_bounds():
    visual_request = request()
    out_of_bounds = RegionMask(
        region=EditRegion.HAIR,
        spans=(MaskSpan(y=1, x_start=2, x_end=9),),
    )
    result = evaluate(
        visual_request=visual_request,
        mask_candidate=candidate(visual_request, regions=(out_of_bounds,)),
    )
    assert MaskValidationReason.SPAN_OUT_OF_BOUNDS in result.reasons


def test_candidate_mask_cannot_overlap_itself():
    visual_request = request()
    overlap = RegionMask(
        region=EditRegion.HAIR,
        spans=(
            MaskSpan(y=1, x_start=2, x_end=5),
            MaskSpan(y=1, x_start=4, x_end=6),
        ),
    )
    result = evaluate(
        visual_request=visual_request,
        mask_candidate=candidate(visual_request, regions=(overlap,)),
    )
    assert MaskValidationReason.CANDIDATE_SPAN_OVERLAP in result.reasons


def test_candidate_pixels_must_be_subset_of_exact_authorized_region_geometry():
    visual_request = request()
    escape = RegionMask(
        region=EditRegion.HAIR,
        spans=(MaskSpan(y=1, x_start=0, x_end=6),),
    )
    result = evaluate(
        visual_request=visual_request,
        mask_candidate=candidate(visual_request, regions=(escape,)),
    )
    assert MaskValidationReason.CANDIDATE_ESCAPES_AUTHORIZATION in result.reasons


def test_mask_digest_is_recomputed_and_must_match_untrusted_candidate_content():
    visual_request = request()
    valid = candidate(visual_request)
    tampered = valid.model_copy(update={"mask_sha256": "f" * 64})
    result = evaluate(visual_request=visual_request, mask_candidate=tampered)
    assert result.reasons == (MaskValidationReason.MASK_HASH_MISMATCH,)


def test_mask_fingerprint_is_deterministic_across_span_input_order():
    visual_request = request()
    first = candidate(
        visual_request,
        regions=(RegionMask(region=EditRegion.HAIR, spans=(
            MaskSpan(y=2, x_start=2, x_end=6),
            MaskSpan(y=1, x_start=2, x_end=6),
        )),),
    )
    second = candidate(
        visual_request,
        regions=(RegionMask(region=EditRegion.HAIR, spans=(
            MaskSpan(y=1, x_start=2, x_end=6),
            MaskSpan(y=2, x_start=2, x_end=6),
        )),),
    )
    assert first.mask_sha256 == second.mask_sha256


def test_specialist_assisted_and_hybrid_masks_require_specialist_provenance():
    visual_request = request()
    for mode in (MaskMode.SPECIALIST_ASSISTED, MaskMode.HYBRID):
        with pytest.raises(ValueError, match="specialist_actor_id"):
            MaskCandidate(
                mask_id="BAD",
                request_id=visual_request.request_id,
                tenant_id=TENANT,
                session_id=SESSION,
                source_asset_id="IMG-32",
                option_id="LOOK-A",
                mode=mode,
                width=8,
                height=8,
                region_masks=(RegionMask(region=EditRegion.HAIR, spans=(MaskSpan(y=1, x_start=1, x_end=2),)),),
                mask_sha256="0" * 64,
            )


def test_specialist_assisted_mask_with_provenance_can_pass_same_pixel_scope_gate():
    visual_request = request()
    assisted = candidate(
        visual_request,
        mode=MaskMode.SPECIALIST_ASSISTED,
        specialist_actor_id="SP-32",
    )
    result = evaluate(visual_request=visual_request, mask_candidate=assisted)
    assert result.provider_dispatch_allowed is True


def test_blocked_mask_decision_cannot_be_promoted_to_provider_dispatch():
    visual_request = request()
    invalid = candidate(visual_request).model_copy(update={"mask_sha256": "a" * 64})
    decision = evaluate(visual_request=visual_request, mask_candidate=invalid)
    with pytest.raises(MaskValidationRejected, match="MASK_HASH_MISMATCH"):
        decision.require_provider_dispatchable()
