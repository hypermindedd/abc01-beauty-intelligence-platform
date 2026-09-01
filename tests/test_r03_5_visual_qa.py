from __future__ import annotations

import pytest

from abc_core.visual_compositor import LockedCompositeArtifact
from abc_core.visual_qa import (
    QaDimension,
    QaEvidenceOrigin,
    QaFinding,
    QaFindingStatus,
    RetryBudget,
    VisualQaAction,
    VisualQaEngine,
    VisualQaEvidenceBundle,
    VisualQaReason,
    required_dimensions_for_services,
)


SHA = "a" * 64


def composite(**overrides) -> LockedCompositeArtifact:
    data = dict(
        composite_id="CMP-1",
        quarantine_id="Q-1",
        dispatch_id="D-1",
        request_id="REQ-1",
        tenant_id="T-1",
        session_id="S-1",
        source_asset_id="ASSET-1",
        option_id="LOOK-A",
        canonical_revision=9,
        mask_id="MASK-1",
        mask_sha256="b" * 64,
        authorization_sha256="c" * 64,
        source_sha256="d" * 64,
        raw_sha256="e" * 64,
        width=2,
        height=2,
        channels=3,
        composite_pixel_sha256=SHA,
        locked_pixel_verification_sha256="f" * 64,
        edited_pixel_count=2,
        locked_pixel_count=2,
        pixels=b"\x00" * 12,
    )
    data.update(overrides)
    return LockedCompositeArtifact(**data)


def bundle(comp, statuses, *, sha=None, comp_id=None):
    findings = tuple(
        QaFinding(dim, status, f"evidence for {dim.value}", QaEvidenceOrigin.MODEL_EVALUATION)
        for dim, status in statuses.items()
    )
    return VisualQaEvidenceBundle(
        composite_id=comp_id or comp.composite_id,
        composite_pixel_sha256=sha or comp.composite_pixel_sha256,
        findings=findings,
    )


def all_pass(service_ids):
    return {dim: QaFindingStatus.PASS for dim in required_dimensions_for_services(service_ids)}


def test_hair_color_requires_identity_and_hair_shape_reality_without_anatomy_inference():
    required = required_dimensions_for_services(("SVC-02-001",))
    assert QaDimension.REQUESTED_CHANGE_FIDELITY in required
    assert QaDimension.IDENTITY_CONTINUITY in required
    assert QaDimension.HAIR_SHAPE_SOURCE_REALITY in required
    assert QaDimension.UNRELATED_REGION_INTEGRITY in required
    assert QaDimension.DOMAIN_SOURCE_REALITY in required
    assert QaDimension.HAND_GEOMETRY_CONTINUITY not in required


def test_makeup_requires_face_geometry_and_nails_require_hand_geometry():
    makeup = required_dimensions_for_services(("SVC-03-001",))
    nails = required_dimensions_for_services(("SVC-04-001",))
    assert QaDimension.FACE_GEOMETRY_CONTINUITY in makeup
    assert QaDimension.HAND_GEOMETRY_CONTINUITY in nails


def test_mens_grooming_requires_facial_hair_source_reality():
    required = required_dimensions_for_services(("SVC-05-001",))
    assert QaDimension.FACIAL_HAIR_SOURCE_REALITY in required
    assert QaDimension.HAIR_SHAPE_SOURCE_REALITY in required


def test_multi_service_scope_is_additive_not_weakening():
    required = required_dimensions_for_services(("SVC-03-001", "SVC-04-001"))
    assert QaDimension.FACE_GEOMETRY_CONTINUITY in required
    assert QaDimension.HAND_GEOMETRY_CONTINUITY in required


def test_all_required_pass_makes_only_a_decision_preview_candidate():
    comp = composite()
    services = ("SVC-03-001",)
    decision = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=services,
        evidence=bundle(comp, all_pass(services)),
        budget=RetryBudget(attempt=1, max_attempts=2),
    )
    assert decision.action is VisualQaAction.QA_APPROVED
    assert decision.eligible_for_decision_preview_candidate is True
    decision.require_qa_approved()


def test_missing_evidence_never_silently_passes():
    comp = composite()
    decision = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=("SVC-03-001",),
        evidence=bundle(comp, {QaDimension.REQUESTED_CHANGE_FIDELITY: QaFindingStatus.PASS}),
        budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.HONEST_LIMITATION
    assert VisualQaReason.REQUIRED_DIMENSION_MISSING in decision.reasons
    assert decision.eligible_for_decision_preview_candidate is False


def test_unknown_is_honest_limitation_not_fake_pass_or_retry():
    comp = composite()
    services = ("SVC-01-001",)
    statuses = all_pass(services)
    statuses[QaDimension.IDENTITY_CONTINUITY] = QaFindingStatus.UNKNOWN
    decision = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=services,
        evidence=bundle(comp, statuses),
        budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.HONEST_LIMITATION
    assert QaDimension.IDENTITY_CONTINUITY in decision.unknown_dimensions


def test_specialist_check_is_not_auto_passed_by_qa():
    comp = composite()
    services = ("SVC-02-001",)
    statuses = all_pass(services)
    statuses[QaDimension.DOMAIN_SOURCE_REALITY] = QaFindingStatus.REQUIRES_SPECIALIST_CHECK
    decision = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=services,
        evidence=bundle(comp, statuses),
        budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.SPECIALIST_CHECK
    assert decision.eligible_for_decision_preview_candidate is False


def test_failure_retries_only_while_bounded_budget_remains():
    comp = composite()
    services = ("SVC-05-001",)
    statuses = all_pass(services)
    statuses[QaDimension.FACIAL_HAIR_SOURCE_REALITY] = QaFindingStatus.FAIL
    first = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=services,
        evidence=bundle(comp, statuses),
        budget=RetryBudget(attempt=1, max_attempts=2),
    )
    last = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=services,
        evidence=bundle(comp, statuses),
        budget=RetryBudget(attempt=2, max_attempts=2),
    )
    assert first.action is VisualQaAction.RETRY
    assert last.action is VisualQaAction.REJECT


def test_cross_composite_or_stale_evidence_is_rejected_immediately():
    comp = composite()
    decision = VisualQaEngine().evaluate(
        composite=comp,
        service_ids=("SVC-01-001",),
        evidence=bundle(comp, all_pass(("SVC-01-001",)), sha="9" * 64),
        budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.REJECT
    assert decision.reasons == (VisualQaReason.EVIDENCE_BINDING_MISMATCH,)


def test_duplicate_dimension_findings_are_invalid():
    comp = composite()
    finding = QaFinding(
        QaDimension.REQUESTED_CHANGE_FIDELITY,
        QaFindingStatus.PASS,
        "observed",
        QaEvidenceOrigin.DETERMINISTIC,
    )
    with pytest.raises(ValueError, match="duplicate"):
        VisualQaEvidenceBundle(comp.composite_id, comp.composite_pixel_sha256, (finding, finding))


def test_retry_budget_cannot_be_unbounded_or_invalid():
    with pytest.raises(ValueError, match="between 1 and 3"):
        RetryBudget(attempt=1, max_attempts=99)
    with pytest.raises(ValueError, match="inside"):
        RetryBudget(attempt=3, max_attempts=2)
