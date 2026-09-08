from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from abc_core.service_intelligence import ServiceResolutionError
from abc_core.visual_compositor import LockedCompositeArtifact
from abc_core.visual_qa import (
    QaDimension, QaEvidenceOrigin, QaFinding, QaFindingStatus, RetryBudget,
    VisualQaAction, VisualQaEngine, VisualQaEvidenceBundle,
    required_dimensions_for_services,
)


def composite() -> LockedCompositeArtifact:
    pixels = bytes(range(12))
    return LockedCompositeArtifact(
        composite_id="CMP-1", quarantine_id="Q-1", dispatch_id="D-1",
        request_id="REQ-1", tenant_id="T-1", session_id="S-1",
        source_asset_id="ASSET-1", option_id="LOOK-A", canonical_revision=9,
        mask_id="MASK-1", mask_sha256="b" * 64,
        authorization_sha256="c" * 64, source_sha256="d" * 64,
        raw_sha256="e" * 64, width=2, height=2, channels=3,
        composite_pixel_sha256=hashlib.sha256(pixels).hexdigest(),
        locked_pixel_verification_sha256="f" * 64,
        edited_pixel_count=2, locked_pixel_count=2, pixels=pixels,
    )


def evidence(comp: LockedCompositeArtifact, service_ids=("SVC-01-001",)) -> VisualQaEvidenceBundle:
    findings = tuple(
        QaFinding(dim, QaFindingStatus.PASS, "explicit test finding", QaEvidenceOrigin.MODEL_EVALUATION)
        for dim in required_dimensions_for_services(service_ids)
    )
    return VisualQaEvidenceBundle(
        composite_id=comp.composite_id,
        composite_pixel_sha256=comp.composite_pixel_sha256,
        findings=findings,
        request_id=comp.request_id, tenant_id=comp.tenant_id,
        session_id=comp.session_id, source_asset_id=comp.source_asset_id,
        option_id=comp.option_id, canonical_revision=comp.canonical_revision,
        service_ids=service_ids,
    )


def test_unknown_forbidden_and_empty_scopes_cannot_be_resolved_by_prefix():
    for ids in ((), ("SVC-01-999",), ("SVC-03-008",), ("CTRL-011",)):
        with pytest.raises(ServiceResolutionError):
            required_dimensions_for_services(ids)


def test_controlled_services_inherit_exact_component_qa_obligations():
    expected = {
        "CTRL-001": QaDimension.HAIR_SHAPE_SOURCE_REALITY,
        "CTRL-002": QaDimension.FACE_GEOMETRY_CONTINUITY,
        "CTRL-003": QaDimension.HAND_GEOMETRY_CONTINUITY,
        "CTRL-004": QaDimension.FACIAL_HAIR_SOURCE_REALITY,
        "CTRL-005": QaDimension.HAIR_SHAPE_SOURCE_REALITY,
        "CTRL-006": QaDimension.HAIR_SHAPE_SOURCE_REALITY,
        "CTRL-007": QaDimension.HAIR_SHAPE_SOURCE_REALITY,
        "CTRL-008": QaDimension.FACE_GEOMETRY_CONTINUITY,
        "CTRL-009": QaDimension.HAND_GEOMETRY_CONTINUITY,
        "CTRL-010": QaDimension.HAND_GEOMETRY_CONTINUITY,
    }
    for service_id, dimension in expected.items():
        assert dimension in required_dimensions_for_services((service_id,))


def test_claimed_composite_digest_cannot_replace_actual_raster_integrity():
    comp = composite()
    altered = replace(comp, pixels=b"\xff" + comp.pixels[1:])
    decision = VisualQaEngine().evaluate(
        composite=altered, service_ids=("SVC-01-001",),
        evidence=evidence(comp), budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.REJECT
    assert decision.eligible_for_decision_preview_candidate is False


def test_qa_evidence_cannot_be_reused_for_a_different_request_context():
    comp = composite()
    borrowed = replace(evidence(comp), request_id="OTHER-REQUEST")
    decision = VisualQaEngine().evaluate(
        composite=comp, service_ids=("SVC-01-001",),
        evidence=borrowed, budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.REJECT
    assert decision.eligible_for_decision_preview_candidate is False


def test_qa_evidence_cannot_be_reused_for_a_reduced_service_scope():
    comp = composite()
    borrowed = evidence(comp, ("SVC-01-001", "SVC-04-001"))
    decision = VisualQaEngine().evaluate(
        composite=comp, service_ids=("SVC-01-001",),
        evidence=borrowed, budget=RetryBudget(attempt=1),
    )
    assert decision.action is VisualQaAction.REJECT
    assert decision.eligible_for_decision_preview_candidate is False
