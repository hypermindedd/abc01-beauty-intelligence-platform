from __future__ import annotations

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
from abc_core.visual_request import (
    EditRegion,
    MediaConsentState,
    VisualGateReason,
    VisualGateStatus,
    VisualInputQuality,
    VisualPreviewRequest,
    VisualRequestGate,
    VisualRequestRejected,
)


TENANT = "T-R031"
SERVICE = "SVC-01-001"
SYSTEM = ActorContext(actor_type=ActorType.SYSTEM, actor_id="AG-05", tenant_id=TENANT)
SPECIALIST = ActorContext(actor_type=ActorType.SPECIALIST, actor_id="SP-31", tenant_id=TENANT)
CLIENT = ActorContext(actor_type=ActorType.CLIENT, actor_id="CL-31", tenant_id=TENANT)


def enabled_capabilities() -> CapabilityState:
    return CapabilityState(
        external_visual_provider=True,
        deterministic_full_frame_lock_compositor=True,
    )


def salon_config(*, feature: bool = True, services: tuple[str, ...] = (SERVICE,)) -> SalonConfig:
    return SalonConfig(
        tenant_id=TENANT,
        salon_id="SALON-31",
        display_name="R03 Test Salon",
        enabled_service_ids=services,
        enabled_feature_ids=("VISUAL_PREVIEW",) if feature else (),
    )


def canonical_state(*, source_media_type: str = "image/jpeg", selected_option: str = "LOOK-A") -> SalonSessionState:
    mutation = SessionMutationEngine()
    state = SalonSessionState(tenant_id=TENANT, session_id="SESSION-31")
    state = mutation.set_request(
        state,
        SYSTEM,
        RequestState(request_id="REQ-SESSION", service_ids=(SERVICE,)),
    )
    state = mutation.add_input_asset(
        state,
        CLIENT,
        InputAsset(asset_id="IMG-1", media_type=source_media_type),
    )
    state = mutation.set_analysis(
        state,
        SPECIALIST,
        AnalysisState(
            analysis_id="AN-31",
            capture_sufficient=True,
            reviewed_by_specialist=True,
        ),
    )
    state = mutation.publish_recommendations(
        state,
        SYSTEM,
        RecommendationSet(
            recommendation_set_id="REC-31",
            core_options=(
                RecommendationOption(
                    option_id="LOOK-A",
                    title="Best Fit",
                    role=RecommendationRole.BEST_FIT,
                ),
                RecommendationOption(
                    option_id="LOOK-B",
                    title="Alternative",
                    role=RecommendationRole.ALTERNATIVE,
                ),
            ),
        ),
    )
    state = mutation.select_option(
        state,
        CLIENT,
        ClientSelection(selection_id="SEL-31", option_id=selected_option),
    )
    return state


def preview_request(
    *,
    source_asset_id: str = "IMG-1",
    option_id: str = "LOOK-A",
    service_ids: tuple[str, ...] = (SERVICE,),
    regions: tuple[EditRegion, ...] = (EditRegion.HAIR,),
    source_consent: MediaConsentState = MediaConsentState.GRANTED,
    processing_consent: MediaConsentState = MediaConsentState.GRANTED,
    quality: VisualInputQuality = VisualInputQuality.USABLE,
    tenant_id: str = TENANT,
    session_id: str = "SESSION-31",
) -> VisualPreviewRequest:
    return VisualPreviewRequest(
        request_id="VR-31",
        tenant_id=tenant_id,
        session_id=session_id,
        source_asset_id=source_asset_id,
        option_id=option_id,
        service_ids=service_ids,
        requested_edit_regions=regions,
        source_media_consent=source_consent,
        provider_processing_consent=processing_consent,
        input_quality=quality,
    )


def evaluate(*, state=None, request=None, config=None, allowed=(EditRegion.HAIR,), capabilities=None):
    state = state or canonical_state()
    request = request or preview_request()
    config = config or salon_config()
    gate = VisualRequestGate(capabilities=capabilities or enabled_capabilities())
    return gate.evaluate(
        request=request,
        state=state,
        salon_config=config,
        allowed_edit_regions=allowed,
    )


def test_current_capability_truth_blocks_provider_dispatch_fail_closed():
    decision = evaluate(capabilities=CAPABILITIES)
    assert decision.status is VisualGateStatus.BLOCKED
    assert decision.dispatch_allowed is False
    assert decision.reasons == (
        VisualGateReason.EXTERNAL_PROVIDER_UNAVAILABLE,
        VisualGateReason.DETERMINISTIC_COMPOSITOR_UNAVAILABLE,
    )


def test_dispatch_candidate_passes_only_when_every_r03_1_gate_is_satisfied_and_state_is_unchanged():
    state = canonical_state()
    before = state.canonical_snapshot()
    decision = evaluate(state=state)
    assert decision.status is VisualGateStatus.PASS
    assert decision.dispatch_allowed is True
    assert decision.reasons == ()
    assert decision.canonical_revision == state.revision
    assert state.canonical_snapshot() == before


def test_consent_must_be_explicitly_granted_for_source_and_provider_processing():
    decision = evaluate(request=preview_request(source_consent=MediaConsentState.DENIED))
    assert decision.reasons == (VisualGateReason.CONSENT_NOT_GRANTED,)
    with __import__("pytest").raises(VisualRequestRejected, match="CONSENT_NOT_GRANTED"):
        decision.require_dispatchable()


def test_limited_or_unreadable_input_cannot_reach_provider_dispatch():
    limited = evaluate(request=preview_request(quality=VisualInputQuality.LIMITED))
    unreadable = evaluate(request=preview_request(quality=VisualInputQuality.UNREADABLE))
    assert limited.reasons == (VisualGateReason.INPUT_QUALITY_INSUFFICIENT,)
    assert unreadable.reasons == (VisualGateReason.INPUT_QUALITY_INSUFFICIENT,)


def test_requested_edit_scope_must_be_nonempty_and_subset_of_governed_authorization():
    empty = evaluate(request=preview_request(regions=()))
    unrelated = evaluate(request=preview_request(regions=(EditRegion.MAKEUP_FACE,)))
    assert empty.reasons == (VisualGateReason.EDIT_SCOPE_EMPTY,)
    assert unrelated.reasons == (VisualGateReason.EDIT_SCOPE_NOT_AUTHORIZED,)


def test_unresolved_s2_or_s3_professional_safety_state_blocks_dispatch_but_resolved_s2_can_continue():
    mutation = SessionMutationEngine()
    state = mutation.add_safety_flag(
        canonical_state(),
        SYSTEM,
        SafetyFlag(flag_id="S2-31", tier=SafetyTier.S2, reason="professional check"),
    )
    blocked = evaluate(state=state)
    assert blocked.reasons == (VisualGateReason.UNRESOLVED_PROFESSIONAL_SAFETY_CHECK,)

    resolved = mutation.resolve_safety_flag(state, SPECIALIST, "S2-31", "checked")
    allowed = evaluate(state=resolved)
    assert allowed.dispatch_allowed is True


def test_s1_attention_does_not_impersonate_professional_s2_s3_block():
    state = SessionMutationEngine().add_safety_flag(
        canonical_state(),
        SYSTEM,
        SafetyFlag(flag_id="S1-31", tier=SafetyTier.S1, reason="attention"),
    )
    assert evaluate(state=state).dispatch_allowed is True


def test_preview_must_reference_the_client_selected_active_direction():
    state = canonical_state(selected_option="LOOK-B")
    decision = evaluate(state=state, request=preview_request(option_id="LOOK-A"))
    assert decision.reasons == (VisualGateReason.OPTION_SELECTION_MISMATCH,)

    missing = evaluate(request=preview_request(option_id="LOOK-X"))
    assert VisualGateReason.OPTION_SELECTION_MISMATCH in missing.reasons
    assert VisualGateReason.OPTION_NOT_ACTIVE in missing.reasons


def test_tenant_feature_and_service_configuration_are_fail_closed():
    tenant = evaluate(request=preview_request(tenant_id="OTHER-TENANT"))
    feature = evaluate(config=salon_config(feature=False))
    service = evaluate(config=salon_config(services=()))
    assert tenant.reasons == (VisualGateReason.TENANT_MISMATCH,)
    assert feature.reasons == (VisualGateReason.VISUAL_FEATURE_DISABLED,)
    assert service.reasons == (VisualGateReason.SERVICE_DISABLED_FOR_TENANT,)


def test_source_asset_must_exist_and_be_an_image():
    missing = evaluate(request=preview_request(source_asset_id="MISSING"))
    wrong_type = evaluate(state=canonical_state(source_media_type="text/plain"))
    assert missing.reasons == (VisualGateReason.SOURCE_ASSET_MISSING,)
    assert wrong_type.reasons == (VisualGateReason.SOURCE_ASSET_NOT_IMAGE,)


def test_visual_service_scope_cannot_escape_the_canonical_session_request():
    second_service = "SVC-02-001"
    request = preview_request(service_ids=(SERVICE, second_service))
    config = salon_config(services=(SERVICE, second_service))
    decision = evaluate(request=request, config=config)
    assert decision.reasons == (VisualGateReason.SERVICE_SCOPE_MISMATCH,)
