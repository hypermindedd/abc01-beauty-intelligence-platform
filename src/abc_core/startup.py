from __future__ import annotations

from pathlib import Path

from .baseline import BaselineReport, load_manifest, validate_manifest


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_startup_gate(root: Path | None = None) -> BaselineReport:
    base = root or repository_root()
    manifest = base / "manifests" / "ABC_PZ_R02_INPUT_BASELINE_MANIFEST_v1.0.0.json"
    if not manifest.is_file():
        raise RuntimeError("required Productization baseline manifest is missing")
    return validate_manifest(load_manifest(manifest))
