from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from abc_core.state import SalonSessionState
from abc_core.visual_request import VisualGateDecision, VisualPreviewRequest

from .contracts import FrameLockPolicy, MaskAuthorization, MaskCandidate, MaskSpan, RegionMask


class MaskValidationStatus(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class MaskValidationReason(StrEnum):
    R03_1_PREFLIGHT_BLOCKED = "R03_1_PREFLIGHT_BLOCKED"
    R03_1_PREFLIGHT_BINDING_MISMATCH = "R03_1_PREFLIGHT_BINDING_MISMATCH"
    STALE_CANONICAL_REVISION = "STALE_CANONICAL_REVISION"
    AUTHORIZATION_BINDING_MISMATCH = "AUTHORIZATION_BINDING_MISMATCH"
    CANDIDATE_BINDING_MISMATCH = "CANDIDATE_BINDING_MISMATCH"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    AUTHORIZATION_REGION_SCOPE_MISMATCH = "AUTHORIZATION_REGION_SCOPE_MISMATCH"
    CANDIDATE_REGION_SCOPE_MISMATCH = "CANDIDATE_REGION_SCOPE_MISMATCH"
    SPAN_OUT_OF_BOUNDS = "SPAN_OUT_OF_BOUNDS"
    CANDIDATE_SPAN_OVERLAP = "CANDIDATE_SPAN_OVERLAP"
    CANDIDATE_ESCAPES_AUTHORIZATION = "CANDIDATE_ESCAPES_AUTHORIZATION"
    MASK_HASH_MISMATCH = "MASK_HASH_MISMATCH"


class MaskValidationRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatedMask:
    mask_id: str
    authorization_id: str
    request_id: str
    tenant_id: str
    session_id: str
    source_asset_id: str
    option_id: str
    canonical_revision: int
    width: int
    height: int
    regions: tuple[str, ...]
    mask_sha256: str
    authorization_sha256: str
    lock_policy: FrameLockPolicy


@dataclass(frozen=True)
class MaskValidationDecision:
    status: MaskValidationStatus
    provider_dispatch_allowed: bool
    reasons: tuple[MaskValidationReason, ...]
    validated_mask: ValidatedMask | None = None

    def require_provider_dispatchable(self) -> ValidatedMask:
        if not self.provider_dispatch_allowed or self.validated_mask is None:
            values = ", ".join(reason.value for reason in self.reasons)
            raise MaskValidationRejected(f"visual provider dispatch blocked by R03.2: {values}")
        return self.validated_mask


def _canonical_region_masks(region_masks: tuple[RegionMask, ...]) -> list[dict[str, object]]:
    return [
        {
            "region": region_mask.region.value,
            "spans": [
                {"y": span.y, "x_start": span.x_start, "x_end": span.x_end}
                for span in sorted(
                    region_mask.spans,
                    key=lambda item: (item.y, item.x_start, item.x_end),
                )
            ],
        }
        for region_mask in sorted(region_masks, key=lambda item: item.region.value)
    ]


def fingerprint_mask_candidate(candidate: MaskCandidate) -> str:
    payload = {
        "mask_id": candidate.mask_id,
        "request_id": candidate.request_id,
        "tenant_id": candidate.tenant_id,
        "session_id": candidate.session_id,
        "source_asset_id": candidate.source_asset_id,
        "option_id": candidate.option_id,
        "mode": candidate.mode.value,
        "width": candidate.width,
        "height": candidate.height,
        "region_masks": _canonical_region_masks(candidate.region_masks),
        "specialist_actor_id": candidate.specialist_actor_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fingerprint_authorization(authorization: MaskAuthorization) -> str:
    payload = {
        "authorization_id": authorization.authorization_id,
        "request_id": authorization.request_id,
        "tenant_id": authorization.tenant_id,
        "session_id": authorization.session_id,
        "source_asset_id": authorization.source_asset_id,
        "option_id": authorization.option_id,
        "width": authorization.width,
        "height": authorization.height,
        "region_masks": _canonical_region_masks(authorization.region_masks),
        "policy": authorization.policy.value,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _span_in_bounds(span: MaskSpan, width: int, height: int) -> bool:
    return 0 <= span.y < height and 0 <= span.x_start < span.x_end <= width


def _has_overlap(spans: tuple[MaskSpan, ...]) -> bool:
    by_row: dict[int, list[MaskSpan]] = {}
    for span in spans:
        by_row.setdefault(span.y, []).append(span)
    for row_spans in by_row.values():
        ordered = sorted(row_spans, key=lambda item: (item.x_start, item.x_end))
        previous_end = -1
        for span in ordered:
            if span.x_start < previous_end:
                return True
            previous_end = max(previous_end, span.x_end)
    return False


def _merged_intervals(spans: tuple[MaskSpan, ...]) -> dict[int, tuple[tuple[int, int], ...]]:
    by_row: dict[int, list[tuple[int, int]]] = {}
    for span in spans:
        by_row.setdefault(span.y, []).append((span.x_start, span.x_end))
    merged: dict[int, tuple[tuple[int, int], ...]] = {}
    for y, intervals in by_row.items():
        ordered = sorted(intervals)
        row: list[list[int]] = []
        for start, end in ordered:
            if not row or start > row[-1][1]:
                row.append([start, end])
            else:
                row[-1][1] = max(row[-1][1], end)
        merged[y] = tuple((start, end) for start, end in row)
    return merged


def _candidate_is_subset(candidate: RegionMask, authorization: RegionMask) -> bool:
    allowed = _merged_intervals(authorization.spans)
    for span in candidate.spans:
        if not any(start <= span.x_start and span.x_end <= end for start, end in allowed.get(span.y, ())):
            return False
    return True


@dataclass(frozen=True)
class MaskValidationGate:
    """R03.2 exact pixel-scope gate between R03.1 and visual-provider invocation."""

    def evaluate(
        self,
        *,
        preflight: VisualGateDecision,
        request: VisualPreviewRequest,
        state: SalonSessionState,
        authorization: MaskAuthorization,
        candidate: MaskCandidate,
    ) -> MaskValidationDecision:
        before = state.canonical_snapshot()
        reasons: list[MaskValidationReason] = []

        if not preflight.dispatch_allowed:
            reasons.append(MaskValidationReason.R03_1_PREFLIGHT_BLOCKED)

        preflight_binding = (
            preflight.request_id,
            preflight.tenant_id,
            preflight.session_id,
            preflight.source_asset_id,
            preflight.option_id,
            preflight.service_ids,
            preflight.requested_edit_regions,
        )
        request_binding = (
            request.request_id,
            request.tenant_id,
            request.session_id,
            request.source_asset_id,
            request.option_id,
            request.service_ids,
            request.requested_edit_regions,
        )
        if preflight_binding != request_binding:
            reasons.append(MaskValidationReason.R03_1_PREFLIGHT_BINDING_MISMATCH)

        if state.revision != preflight.canonical_revision:
            reasons.append(MaskValidationReason.STALE_CANONICAL_REVISION)

        expected_binding = (
            request.request_id,
            request.tenant_id,
            request.session_id,
            request.source_asset_id,
            request.option_id,
        )
        authorization_binding = (
            authorization.request_id,
            authorization.tenant_id,
            authorization.session_id,
            authorization.source_asset_id,
            authorization.option_id,
        )
        if authorization_binding != expected_binding:
            reasons.append(MaskValidationReason.AUTHORIZATION_BINDING_MISMATCH)

        candidate_binding = (
            candidate.request_id,
            candidate.tenant_id,
            candidate.session_id,
            candidate.source_asset_id,
            candidate.option_id,
        )
        if candidate_binding != expected_binding:
            reasons.append(MaskValidationReason.CANDIDATE_BINDING_MISMATCH)

        if candidate.width != authorization.width or candidate.height != authorization.height:
            reasons.append(MaskValidationReason.DIMENSION_MISMATCH)

        requested_regions = set(request.requested_edit_regions)
        authorization_regions = {item.region for item in authorization.region_masks}
        candidate_regions = {item.region for item in candidate.region_masks}
        if authorization_regions != requested_regions:
            reasons.append(MaskValidationReason.AUTHORIZATION_REGION_SCOPE_MISMATCH)
        if candidate_regions != requested_regions:
            reasons.append(MaskValidationReason.CANDIDATE_REGION_SCOPE_MISMATCH)

        all_region_masks = authorization.region_masks + candidate.region_masks
        if any(
            not _span_in_bounds(span, authorization.width, authorization.height)
            for region_mask in all_region_masks
            for span in region_mask.spans
        ):
            reasons.append(MaskValidationReason.SPAN_OUT_OF_BOUNDS)

        if any(_has_overlap(region_mask.spans) for region_mask in candidate.region_masks):
            reasons.append(MaskValidationReason.CANDIDATE_SPAN_OVERLAP)

        authorization_by_region = {item.region: item for item in authorization.region_masks}
        if authorization_regions == requested_regions and candidate_regions == requested_regions:
            for region_mask in candidate.region_masks:
                authorized = authorization_by_region[region_mask.region]
                if not _candidate_is_subset(region_mask, authorized):
                    reasons.append(MaskValidationReason.CANDIDATE_ESCAPES_AUTHORIZATION)
                    break

        computed_hash = fingerprint_mask_candidate(candidate)
        if candidate.mask_sha256 != computed_hash:
            reasons.append(MaskValidationReason.MASK_HASH_MISMATCH)

        if state.canonical_snapshot() != before:
            raise RuntimeError("R03.2 mask validation mutated canonical truth state")

        unique_reasons = tuple(dict.fromkeys(reasons))
        if unique_reasons:
            return MaskValidationDecision(
                status=MaskValidationStatus.BLOCKED,
                provider_dispatch_allowed=False,
                reasons=unique_reasons,
            )

        validated = ValidatedMask(
            mask_id=candidate.mask_id,
            authorization_id=authorization.authorization_id,
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            source_asset_id=request.source_asset_id,
            option_id=request.option_id,
            canonical_revision=state.revision,
            width=candidate.width,
            height=candidate.height,
            regions=tuple(sorted(region.value for region in candidate_regions)),
            mask_sha256=computed_hash,
            authorization_sha256=fingerprint_authorization(authorization),
            lock_policy=authorization.policy,
        )
        return MaskValidationDecision(
            status=MaskValidationStatus.PASS,
            provider_dispatch_allowed=True,
            reasons=(),
            validated_mask=validated,
        )
