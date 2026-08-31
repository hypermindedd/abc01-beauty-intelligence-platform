from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from abc_core.capabilities import CAPABILITIES, CapabilityState
from abc_core.state import SafetyTier, SalonSessionState
from abc_core.tenancy import SalonConfig

from .contracts import EditRegion, MediaConsentState, VisualInputQuality, VisualPreviewRequest


class VisualGateStatus(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class VisualGateReason(StrEnum):
    TENANT_MISMATCH = "TENANT_MISMATCH"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    VISUAL_FEATURE_DISABLED = "VISUAL_FEATURE_DISABLED"
    EXTERNAL_PROVIDER_UNAVAILABLE = "EXTERNAL_PROVIDER_UNAVAILABLE"
    DETERMINISTIC_COMPOSITOR_UNAVAILABLE = "DETERMINISTIC_COMPOSITOR_UNAVAILABLE"
    SESSION_REQUEST_MISSING = "SESSION_REQUEST_MISSING"
    SERVICE_SCOPE_MISMATCH = "SERVICE_SCOPE_MISMATCH"
    SERVICE_DISABLED_FOR_TENANT = "SERVICE_DISABLED_FOR_TENANT"
    SOURCE_ASSET_MISSING = "SOURCE_ASSET_MISSING"
    SOURCE_ASSET_NOT_IMAGE = "SOURCE_ASSET_NOT_IMAGE"
    CLIENT_SELECTION_MISSING = "CLIENT_SELECTION_MISSING"
    OPTION_SELECTION_MISMATCH = "OPTION_SELECTION_MISMATCH"
    OPTION_NOT_ACTIVE = "OPTION_NOT_ACTIVE"
    CONSENT_NOT_GRANTED = "CONSENT_NOT_GRANTED"
    INPUT_QUALITY_INSUFFICIENT = "INPUT_QUALITY_INSUFFICIENT"
    EDIT_SCOPE_EMPTY = "EDIT_SCOPE_EMPTY"
    EDIT_SCOPE_NOT_AUTHORIZED = "EDIT_SCOPE_NOT_AUTHORIZED"
    UNRESOLVED_PROFESSIONAL_SAFETY_CHECK = "UNRESOLVED_PROFESSIONAL_SAFETY_CHECK"


class VisualRequestRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class VisualGateDecision:
    status: VisualGateStatus
    dispatch_allowed: bool
    reasons: tuple[VisualGateReason, ...]
    canonical_revision: int
    requested_edit_regions: tuple[EditRegion, ...]

    def require_dispatchable(self) -> None:
        if not self.dispatch_allowed:
            values = ", ".join(reason.value for reason in self.reasons)
            raise VisualRequestRejected(f"visual provider dispatch blocked: {values}")


@dataclass(frozen=True)
class VisualRequestGate:
    """R03.1 fail-closed gate before any external visual provider dispatch.

    This gate is intentionally pure/read-only. It does not call a provider, create
    masks, generate images, mutate canonical session truth or claim readiness.
    """

    capabilities: CapabilityState = CAPABILITIES
    visual_feature_id: str = "VISUAL_PREVIEW"

    def evaluate(
        self,
        *,
        request: VisualPreviewRequest,
        state: SalonSessionState,
        salon_config: SalonConfig,
        allowed_edit_regions: tuple[EditRegion, ...],
    ) -> VisualGateDecision:
        before = state.canonical_snapshot()
        reasons: list[VisualGateReason] = []

        if request.tenant_id != state.tenant_id or salon_config.tenant_id != state.tenant_id:
            reasons.append(VisualGateReason.TENANT_MISMATCH)
        if request.session_id != state.session_id:
            reasons.append(VisualGateReason.SESSION_MISMATCH)

        if self.visual_feature_id not in salon_config.enabled_feature_ids:
            reasons.append(VisualGateReason.VISUAL_FEATURE_DISABLED)

        # Do not spend provider calls if the mandatory post-provider integrity path
        # cannot be completed. Raw provider output must never become the final Preview.
        if not self.capabilities.external_visual_provider:
            reasons.append(VisualGateReason.EXTERNAL_PROVIDER_UNAVAILABLE)
        if not self.capabilities.deterministic_full_frame_lock_compositor:
            reasons.append(VisualGateReason.DETERMINISTIC_COMPOSITOR_UNAVAILABLE)

        request_services = set(request.service_ids)
        if state.request is None:
            reasons.append(VisualGateReason.SESSION_REQUEST_MISSING)
        elif not request_services.issubset(set(state.request.service_ids)):
            reasons.append(VisualGateReason.SERVICE_SCOPE_MISMATCH)

        if not request_services.issubset(set(salon_config.enabled_service_ids)):
            reasons.append(VisualGateReason.SERVICE_DISABLED_FOR_TENANT)

        source_asset = next(
            (asset for asset in state.input_assets if asset.asset_id == request.source_asset_id),
            None,
        )
        if source_asset is None:
            reasons.append(VisualGateReason.SOURCE_ASSET_MISSING)
        elif not source_asset.media_type.lower().startswith("image/"):
            reasons.append(VisualGateReason.SOURCE_ASSET_NOT_IMAGE)

        if state.client_selection is None:
            reasons.append(VisualGateReason.CLIENT_SELECTION_MISSING)
        elif state.client_selection.option_id != request.option_id:
            reasons.append(VisualGateReason.OPTION_SELECTION_MISMATCH)

        active_option_ids: set[str] = set()
        if state.recommendations is not None:
            active_option_ids = {
                option.option_id
                for option in state.recommendations.core_options + state.recommendations.explore_options
            }
        if request.option_id not in active_option_ids:
            reasons.append(VisualGateReason.OPTION_NOT_ACTIVE)

        if (
            request.source_media_consent is not MediaConsentState.GRANTED
            or request.provider_processing_consent is not MediaConsentState.GRANTED
        ):
            reasons.append(VisualGateReason.CONSENT_NOT_GRANTED)

        if request.input_quality not in {VisualInputQuality.USABLE, VisualInputQuality.STRONG}:
            reasons.append(VisualGateReason.INPUT_QUALITY_INSUFFICIENT)

        requested_regions = set(request.requested_edit_regions)
        allowed_regions = set(allowed_edit_regions)
        if not requested_regions:
            reasons.append(VisualGateReason.EDIT_SCOPE_EMPTY)
        elif not requested_regions.issubset(allowed_regions):
            reasons.append(VisualGateReason.EDIT_SCOPE_NOT_AUTHORIZED)

        unresolved_professional = any(
            not flag.resolved and flag.tier in {SafetyTier.S2, SafetyTier.S3}
            for flag in state.safety_flags
        )
        if unresolved_professional:
            reasons.append(VisualGateReason.UNRESOLVED_PROFESSIONAL_SAFETY_CHECK)

        if state.canonical_snapshot() != before:
            raise RuntimeError("R03.1 visual request gate mutated canonical truth state")

        # Preserve deterministic reason order while preventing duplicate reason entries.
        unique_reasons = tuple(dict.fromkeys(reasons))
        dispatch_allowed = not unique_reasons
        return VisualGateDecision(
            status=VisualGateStatus.PASS if dispatch_allowed else VisualGateStatus.BLOCKED,
            dispatch_allowed=dispatch_allowed,
            reasons=unique_reasons,
            canonical_revision=state.revision,
            requested_edit_regions=request.requested_edit_regions,
        )
