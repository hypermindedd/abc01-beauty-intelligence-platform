from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from abc_core.visual_compositor import LockedCompositeArtifact

from .contracts import QaDimension, QaFindingStatus, RetryBudget, VisualQaEvidenceBundle


class VisualQaAction(StrEnum):
    QA_APPROVED = "QA_APPROVED"
    RETRY = "RETRY"
    REJECT = "REJECT"
    HONEST_LIMITATION = "HONEST_LIMITATION"
    SPECIALIST_CHECK = "SPECIALIST_CHECK"


class VisualQaReason(StrEnum):
    EVIDENCE_BINDING_MISMATCH = "EVIDENCE_BINDING_MISMATCH"
    REQUIRED_DIMENSION_MISSING = "REQUIRED_DIMENSION_MISSING"
    REQUIRED_DIMENSION_FAILED = "REQUIRED_DIMENSION_FAILED"
    REQUIRED_DIMENSION_UNKNOWN = "REQUIRED_DIMENSION_UNKNOWN"
    SPECIALIST_CHECK_REQUIRED = "SPECIALIST_CHECK_REQUIRED"


@dataclass(frozen=True)
class VisualQaDecision:
    action: VisualQaAction
    reasons: tuple[VisualQaReason, ...]
    required_dimensions: tuple[QaDimension, ...]
    failed_dimensions: tuple[QaDimension, ...]
    unknown_dimensions: tuple[QaDimension, ...]
    specialist_check_dimensions: tuple[QaDimension, ...]
    eligible_for_decision_preview_candidate: bool
    composite_id: str
    composite_pixel_sha256: str
    attempt: int
    max_attempts: int

    def require_qa_approved(self) -> None:
        if self.action is not VisualQaAction.QA_APPROVED:
            raise RuntimeError(f"visual output is not QA approved: {self.action.value}")


_BASELINE = (
    QaDimension.REQUESTED_CHANGE_FIDELITY,
    QaDimension.UNRELATED_REGION_INTEGRITY,
    QaDimension.DOMAIN_SOURCE_REALITY,
)


def required_dimensions_for_services(service_ids: tuple[str, ...]) -> tuple[QaDimension, ...]:
    """Return conservative QA obligations for the governed service scope.

    This is deliberately additive. Multi-service looks inherit every applicable
    preservation check rather than weakening one domain because another is active.
    Unknown service identifiers keep the baseline and cannot create a silent PASS.
    """

    required = list(_BASELINE)
    for service_id in service_ids:
        if service_id.startswith("SVC-01-"):
            required.extend((QaDimension.IDENTITY_CONTINUITY, QaDimension.HAIR_SHAPE_SOURCE_REALITY))
        elif service_id.startswith("SVC-02-"):
            required.extend((QaDimension.IDENTITY_CONTINUITY, QaDimension.HAIR_SHAPE_SOURCE_REALITY))
        elif service_id.startswith("SVC-03-"):
            required.extend((QaDimension.IDENTITY_CONTINUITY, QaDimension.FACE_GEOMETRY_CONTINUITY))
        elif service_id.startswith("SVC-04-"):
            required.append(QaDimension.HAND_GEOMETRY_CONTINUITY)
        elif service_id.startswith("SVC-05-"):
            required.extend(
                (
                    QaDimension.IDENTITY_CONTINUITY,
                    QaDimension.FACE_GEOMETRY_CONTINUITY,
                    QaDimension.HAIR_SHAPE_SOURCE_REALITY,
                    QaDimension.FACIAL_HAIR_SOURCE_REALITY,
                )
            )
        elif service_id == "CTRL-009":
            required.extend(
                (
                    QaDimension.IDENTITY_CONTINUITY,
                    QaDimension.FACE_GEOMETRY_CONTINUITY,
                    QaDimension.HAIR_SHAPE_SOURCE_REALITY,
                )
            )
    return tuple(dict.fromkeys(required))


@dataclass(frozen=True)
class VisualQaEngine:
    """R03.5 evidence-driven QA gate with bounded retry and honest failure modes.

    The engine does not invent confidence scores and does not itself inspect an
    image. It evaluates explicitly supplied QA findings that are cryptographically
    bound to one R03.4 composite. A live evaluator may be deterministic, model-based,
    specialist-based, or a governed combination; absent evidence can never PASS.
    """

    def evaluate(
        self,
        *,
        composite: LockedCompositeArtifact,
        service_ids: tuple[str, ...],
        evidence: VisualQaEvidenceBundle,
        budget: RetryBudget,
    ) -> VisualQaDecision:
        required = required_dimensions_for_services(service_ids)
        reasons: list[VisualQaReason] = []

        if (
            evidence.composite_id != composite.composite_id
            or evidence.composite_pixel_sha256 != composite.composite_pixel_sha256
        ):
            return VisualQaDecision(
                action=VisualQaAction.REJECT,
                reasons=(VisualQaReason.EVIDENCE_BINDING_MISMATCH,),
                required_dimensions=required,
                failed_dimensions=(),
                unknown_dimensions=(),
                specialist_check_dimensions=(),
                eligible_for_decision_preview_candidate=False,
                composite_id=composite.composite_id,
                composite_pixel_sha256=composite.composite_pixel_sha256,
                attempt=budget.attempt,
                max_attempts=budget.max_attempts,
            )

        by_dimension = {finding.dimension: finding for finding in evidence.findings}
        missing = tuple(dim for dim in required if dim not in by_dimension)
        failed = tuple(
            dim for dim in required if dim in by_dimension and by_dimension[dim].status is QaFindingStatus.FAIL
        )
        unknown = tuple(
            dim for dim in required if dim in by_dimension and by_dimension[dim].status is QaFindingStatus.UNKNOWN
        )
        specialist = tuple(
            dim
            for dim in required
            if dim in by_dimension and by_dimension[dim].status is QaFindingStatus.REQUIRES_SPECIALIST_CHECK
        )

        if missing:
            reasons.append(VisualQaReason.REQUIRED_DIMENSION_MISSING)
        if failed:
            reasons.append(VisualQaReason.REQUIRED_DIMENSION_FAILED)
        if unknown:
            reasons.append(VisualQaReason.REQUIRED_DIMENSION_UNKNOWN)
        if specialist:
            reasons.append(VisualQaReason.SPECIALIST_CHECK_REQUIRED)

        if specialist:
            action = VisualQaAction.SPECIALIST_CHECK
        elif failed:
            action = VisualQaAction.RETRY if budget.retry_available else VisualQaAction.REJECT
        elif missing or unknown:
            action = VisualQaAction.HONEST_LIMITATION
        else:
            action = VisualQaAction.QA_APPROVED

        return VisualQaDecision(
            action=action,
            reasons=tuple(reasons),
            required_dimensions=required,
            failed_dimensions=failed,
            unknown_dimensions=tuple(dict.fromkeys(missing + unknown)),
            specialist_check_dimensions=specialist,
            eligible_for_decision_preview_candidate=action is VisualQaAction.QA_APPROVED,
            composite_id=composite.composite_id,
            composite_pixel_sha256=composite.composite_pixel_sha256,
            attempt=budget.attempt,
            max_attempts=budget.max_attempts,
        )
