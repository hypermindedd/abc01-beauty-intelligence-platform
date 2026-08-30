import copy
import json
from pathlib import Path

import pytest

from abc_core.baseline import BaselineMismatch, validate_manifest
from abc_core.startup import run_startup_gate

ROOT = Path(__file__).resolve().parents[1]


def _data():
    return json.loads((ROOT / "manifests" / "ABC_PZ_R02_INPUT_BASELINE_MANIFEST_v1.0.0.json").read_text())


def test_frozen_baseline_passes():
    report = run_startup_gate(ROOT)
    assert report.ok
    assert report.document_count == 20
    assert report.runtime_knowledge_count == 16
    assert report.canonical_test_range == "ABC-TC-001…132"


def test_tampered_document_version_fails_closed():
    data = copy.deepcopy(_data())
    data["product_docs"][3]["version"] = "9.9.9"
    with pytest.raises(BaselineMismatch):
        validate_manifest(data)


def test_runtime_pass_claim_in_baseline_fails_closed():
    data = copy.deepcopy(_data())
    data["runtime_product_pass_claimed"] = True
    with pytest.raises(BaselineMismatch):
        validate_manifest(data)
