from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import CANONICAL_TEST_LAST, RUNTIME_KNOWLEDGE_COUNT

EXPECTED_DOC_VERSIONS = {
    "ABC-DOC-000": "1.3.0", "ABC-DOC-001": "1.3.0", "ABC-DOC-002": "1.2.0",
    "ABC-DOC-003": "1.1.0", "ABC-DOC-004": "1.1.0", "ABC-DOC-005": "1.2.0",
    "ABC-DOC-006": "1.3.0", "ABC-DOC-007": "1.2.0", "ABC-DOC-008": "1.2.0",
    "ABC-DOC-009": "1.2.0", "ABC-DOC-010": "1.2.0", "ABC-DOC-011": "1.2.0",
    "ABC-DOC-012": "1.3.0", "ABC-DOC-013": "1.3.0", "ABC-DOC-014": "1.3.0",
    "ABC-DOC-015": "1.3.0", "ABC-DOC-016": "1.3.0", "ABC-DOC-016A": "1.0.0",
    "ABC-DOC-018": "1.3.0", "ABC-DOC-900": "1.3.0",
}
EXPECTED_BASELINE_STATUS = "PRODUCTIZATION_BASELINE_FROZEN_FOR_R02_INPUT"
EXPECTED_VISUAL_CONTRACT = "ABC-DOC-016A v1.0.0 PRODUCTIZATION_BASELINE"
EXPECTED_TEST_RANGE = "ABC-TC-001…132"


class BaselineMismatch(RuntimeError):
    pass


@dataclass(frozen=True)
class BaselineReport:
    ok: bool
    document_count: int
    runtime_knowledge_count: int
    canonical_test_range: str
    visual_runtime_contract: str


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(data: dict[str, Any]) -> BaselineReport:
    if data.get("status") != EXPECTED_BASELINE_STATUS:
        raise BaselineMismatch("productization baseline status mismatch")
    if data.get("r02_build_allowed") is not True:
        raise BaselineMismatch("R02 build is not allowed by baseline")
    if data.get("runtime_product_pass_claimed") is not False:
        raise BaselineMismatch("baseline must not claim runtime product PASS")
    if data.get("production_readiness_claimed") is not False:
        raise BaselineMismatch("baseline must not claim production readiness")

    docs = data.get("product_docs") or []
    actual = {row.get("document_id"): row.get("version") for row in docs}
    if actual != EXPECTED_DOC_VERSIONS:
        raise BaselineMismatch("product document version map mismatch")

    runtime_knowledge = data.get("runtime_knowledge") or []
    if len(runtime_knowledge) != RUNTIME_KNOWLEDGE_COUNT:
        raise BaselineMismatch("runtime knowledge count mismatch")
    hashes = [row.get("sha256") for row in runtime_knowledge]
    if any(not h or len(h) != 64 for h in hashes) or len(set(hashes)) != len(hashes):
        raise BaselineMismatch("runtime knowledge hashes invalid or duplicated")

    evaluation = data.get("evaluation") or {}
    if evaluation.get("canonical_test_range") != EXPECTED_TEST_RANGE:
        raise BaselineMismatch("canonical test range mismatch")
    if CANONICAL_TEST_LAST != 132:
        raise BaselineMismatch("compiled canonical test boundary mismatch")

    visual = data.get("visual_runtime_contract")
    if visual != EXPECTED_VISUAL_CONTRACT:
        raise BaselineMismatch("visual runtime contract mismatch")

    groom = data.get("groom_mapping") or {}
    if groom.get("new_groom_service_id") is not None or groom.get("new_groom_control_id") is not None:
        raise BaselineMismatch("invented Groom service/control ID detected")

    return BaselineReport(
        ok=True,
        document_count=len(docs),
        runtime_knowledge_count=len(runtime_knowledge),
        canonical_test_range=evaluation["canonical_test_range"],
        visual_runtime_contract=visual,
    )
