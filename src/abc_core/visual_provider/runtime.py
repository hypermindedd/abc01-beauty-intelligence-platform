from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from abc_core.capabilities import CAPABILITIES, CapabilityState
from abc_core.state import SalonSessionState
from abc_core.tenancy import SalonConfig
from abc_core.visual_mask import (
    FrameLockPolicy,
    MaskAuthorization,
    MaskCandidate,
    MaskValidationGate,
    fingerprint_mask_candidate,
)
from abc_core.visual_request import EditRegion, VisualPreviewRequest, VisualRequestGate

from .contracts import ProviderDispatchEnvelope, SourcePayload, VisualProviderAdapter
from .quarantine import (
    InMemoryRawOutputQuarantine,
    QuarantineDisposition,
    QuarantinedProviderArtifact,
)


class ProviderDispatchStatus(StrEnum):
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    QUARANTINED_REJECTED = "QUARANTINED_REJECTED"


class ProviderDispatchReason(StrEnum):
    R03_1_PREFLIGHT_BLOCKED = "R03_1_PREFLIGHT_BLOCKED"
    R03_2_MASK_BLOCKED = "R03_2_MASK_BLOCKED"
    SOURCE_ASSET_BINDING_MISMATCH = "SOURCE_ASSET_BINDING_MISMATCH"
    SOURCE_MEDIA_TYPE_MISMATCH = "SOURCE_MEDIA_TYPE_MISMATCH"
    INSTRUCTION_EMPTY = "INSTRUCTION_EMPTY"
    PROVIDER_ID_INVALID = "PROVIDER_ID_INVALID"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    RAW_PROVIDER_ID_MISMATCH = "RAW_PROVIDER_ID_MISMATCH"
    RAW_PROVIDER_REQUEST_ID_MISSING = "RAW_PROVIDER_REQUEST_ID_MISSING"
    RAW_PROVIDER_MEDIA_NOT_IMAGE = "RAW_PROVIDER_MEDIA_NOT_IMAGE"
    RAW_PROVIDER_PAYLOAD_EMPTY = "RAW_PROVIDER_PAYLOAD_EMPTY"


@dataclass(frozen=True)
class ProviderDispatchDecision:
    status: ProviderDispatchStatus
    reasons: tuple[ProviderDispatchReason, ...]
    dispatch_fingerprint: str | None = None
    quarantine: QuarantinedProviderArtifact | None = None



def _dispatch_material(
    *,
    provider_id: str,
    request: VisualPreviewRequest,
    source: SourcePayload,
    canonical_revision: int,
    mask_id: str,
    mask_sha256: str,
    authorization_sha256: str,
    mask_width: int,
    mask_height: int,
    lock_policy: FrameLockPolicy,
    instruction_sha256: str,
) -> dict[str, object]:
    return {
        "provider_id": provider_id,
        "request_id": request.request_id,
        "tenant_id": request.tenant_id,
        "session_id": request.session_id,
        "source_asset_id": request.source_asset_id,
        "source_media_type": source.media_type.lower(),
        "source_sha256": source.sha256,
        "option_id": request.option_id,
        "service_ids": sorted(request.service_ids),
        "requested_edit_regions": sorted(region.value for region in request.requested_edit_regions),
        "canonical_revision": canonical_revision,
        "mask_id": mask_id,
        "mask_sha256": mask_sha256,
        "authorization_sha256": authorization_sha256,
        "mask_width": mask_width,
        "mask_height": mask_height,
        "lock_policy": lock_policy.value,
        "instruction_sha256": instruction_sha256,
    }


def fingerprint_dispatch(material: dict[str, object]) -> str:
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _quarantine_id(dispatch_fingerprint: str, raw_sha256: str, provider_request_id: str) -> str:
    material = f"{dispatch_fingerprint}:{raw_sha256}:{provider_request_id}".encode("utf-8")
    return "Q-" + hashlib.sha256(material).hexdigest()[:32]


class ProviderQuarantineRuntime:
    """R03.3: compose R03.1 + R03.2 and quarantine every provider artifact."""

    def __init__(
        self,
        *,
        capabilities: CapabilityState = CAPABILITIES,
        quarantine: InMemoryRawOutputQuarantine | None = None,
    ) -> None:
        self.capabilities = capabilities
        self.quarantine = quarantine if quarantine is not None else InMemoryRawOutputQuarantine()

    def dispatch(
        self,
        *,
        request: VisualPreviewRequest,
        state: SalonSessionState,
        salon_config: SalonConfig,
        allowed_edit_regions: tuple[EditRegion, ...],
        authorization: MaskAuthorization,
        candidate: MaskCandidate,
        source: SourcePayload,
        instruction: str,
        adapter: VisualProviderAdapter,
    ) -> ProviderDispatchDecision:
        before = state.canonical_snapshot()
        reasons: list[ProviderDispatchReason] = []

        preflight = VisualRequestGate(capabilities=self.capabilities).evaluate(
            request=request,
            state=state,
            salon_config=salon_config,
            allowed_edit_regions=allowed_edit_regions,
        )
        if not preflight.dispatch_allowed:
            reasons.append(ProviderDispatchReason.R03_1_PREFLIGHT_BLOCKED)

        mask_decision = MaskValidationGate().evaluate(
            preflight=preflight,
            request=request,
            state=state,
            authorization=authorization,
            candidate=candidate,
        )
        if not mask_decision.provider_dispatch_allowed or mask_decision.validated_mask is None:
            reasons.append(ProviderDispatchReason.R03_2_MASK_BLOCKED)

        source_asset = next(
            (asset for asset in state.input_assets if asset.asset_id == request.source_asset_id),
            None,
        )
        if source.asset_id != request.source_asset_id:
            reasons.append(ProviderDispatchReason.SOURCE_ASSET_BINDING_MISMATCH)
        if source_asset is None or source_asset.media_type.lower() != source.media_type.lower():
            reasons.append(ProviderDispatchReason.SOURCE_MEDIA_TYPE_MISMATCH)
        if not instruction.strip():
            reasons.append(ProviderDispatchReason.INSTRUCTION_EMPTY)

        provider_id = getattr(adapter, "provider_id", "")
        if not isinstance(provider_id, str) or not provider_id.strip():
            reasons.append(ProviderDispatchReason.PROVIDER_ID_INVALID)

        if state.canonical_snapshot() != before:
            raise RuntimeError("R03.3 pre-dispatch validation mutated canonical truth state")

        unique_reasons = tuple(dict.fromkeys(reasons))
        if unique_reasons:
            return ProviderDispatchDecision(
                status=ProviderDispatchStatus.BLOCKED,
                reasons=unique_reasons,
            )

        validated = mask_decision.validated_mask
        assert validated is not None

        if fingerprint_mask_candidate(candidate) != validated.mask_sha256:
            return ProviderDispatchDecision(
                status=ProviderDispatchStatus.BLOCKED,
                reasons=(ProviderDispatchReason.R03_2_MASK_BLOCKED,),
            )

        instruction_sha256 = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
        material = _dispatch_material(
            provider_id=provider_id,
            request=request,
            source=source,
            canonical_revision=validated.canonical_revision,
            mask_id=validated.mask_id,
            mask_sha256=validated.mask_sha256,
            authorization_sha256=validated.authorization_sha256,
            mask_width=validated.width,
            mask_height=validated.height,
            lock_policy=validated.lock_policy,
            instruction_sha256=instruction_sha256,
        )
        dispatch_fingerprint = fingerprint_dispatch(material)
        envelope = ProviderDispatchEnvelope(
            dispatch_id="DSP-" + dispatch_fingerprint[:24],
            dispatch_fingerprint=dispatch_fingerprint,
            provider_id=provider_id,
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            source_asset_id=request.source_asset_id,
            source_media_type=source.media_type.lower(),
            source_sha256=source.sha256,
            option_id=request.option_id,
            service_ids=request.service_ids,
            requested_edit_regions=request.requested_edit_regions,
            canonical_revision=validated.canonical_revision,
            mask_id=validated.mask_id,
            mask_sha256=validated.mask_sha256,
            authorization_sha256=validated.authorization_sha256,
            mask_width=validated.width,
            mask_height=validated.height,
            lock_policy=validated.lock_policy,
            instruction=instruction,
            instruction_sha256=instruction_sha256,
        )

        try:
            raw = adapter.dispatch(envelope, source=source, mask=candidate)
        except Exception:
            if state.canonical_snapshot() != before:
                raise RuntimeError("provider adapter mutated canonical truth state")
            return ProviderDispatchDecision(
                status=ProviderDispatchStatus.FAILED,
                reasons=(ProviderDispatchReason.PROVIDER_ERROR,),
                dispatch_fingerprint=dispatch_fingerprint,
            )

        raw_reasons: list[ProviderDispatchReason] = []
        if raw.provider_id != provider_id:
            raw_reasons.append(ProviderDispatchReason.RAW_PROVIDER_ID_MISMATCH)
        if not raw.provider_request_id:
            raw_reasons.append(ProviderDispatchReason.RAW_PROVIDER_REQUEST_ID_MISSING)
        if not raw.media_type.lower().startswith("image/"):
            raw_reasons.append(ProviderDispatchReason.RAW_PROVIDER_MEDIA_NOT_IMAGE)
        if not raw.content:
            raw_reasons.append(ProviderDispatchReason.RAW_PROVIDER_PAYLOAD_EMPTY)

        raw_sha256 = hashlib.sha256(raw.content).hexdigest()
        unique_raw_reasons = tuple(dict.fromkeys(raw_reasons))
        disposition = QuarantineDisposition.REJECTED if unique_raw_reasons else QuarantineDisposition.HOLD
        artifact = QuarantinedProviderArtifact(
            quarantine_id=_quarantine_id(dispatch_fingerprint, raw_sha256, raw.provider_request_id),
            dispatch_id=envelope.dispatch_id,
            dispatch_fingerprint=dispatch_fingerprint,
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            source_asset_id=request.source_asset_id,
            option_id=request.option_id,
            canonical_revision=validated.canonical_revision,
            provider_adapter_id=provider_id,
            provider_claimed_id=raw.provider_id,
            provider_request_id=raw.provider_request_id,
            mask_id=validated.mask_id,
            mask_sha256=validated.mask_sha256,
            authorization_sha256=validated.authorization_sha256,
            source_sha256=source.sha256,
            raw_sha256=raw_sha256,
            media_type=raw.media_type,
            byte_length=len(raw.content),
            disposition=disposition,
            rejection_reasons=tuple(reason.value for reason in unique_raw_reasons),
            payload=raw.content,
        )
        self.quarantine.put(artifact)

        if state.canonical_snapshot() != before:
            raise RuntimeError("R03.3 provider/quarantine path mutated canonical truth state")

        return ProviderDispatchDecision(
            status=(
                ProviderDispatchStatus.QUARANTINED_REJECTED
                if unique_raw_reasons
                else ProviderDispatchStatus.QUARANTINED
            ),
            reasons=unique_raw_reasons,
            dispatch_fingerprint=dispatch_fingerprint,
            quarantine=artifact,
        )
