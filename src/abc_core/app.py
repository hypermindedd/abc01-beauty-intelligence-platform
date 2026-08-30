from __future__ import annotations

from fastapi import FastAPI

from . import R02_STAGE, __version__
from .capabilities import CAPABILITIES
from .contracts import AGENT_IDS, OUTPUT_IDS
from .startup import run_startup_gate

BASELINE_REPORT = run_startup_gate()

app = FastAPI(title="ABC.01 Beauty Intelligence Core", version=__version__)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "stage": R02_STAGE,
        "engineering_scaffold": True,
        "pilot_ready": False,
        "production_ready": False,
    }


@app.get("/v1/system/build-info")
def build_info() -> dict:
    return {
        "project": "ABC.01",
        "runtime_version": __version__,
        "stage": R02_STAGE,
        "baseline": BASELINE_REPORT.__dict__,
        "agent_ids": AGENT_IDS,
        "output_ids": OUTPUT_IDS,
        "capabilities": CAPABILITIES.public(),
        "readiness_claim": "ENGINEERING_SCAFFOLD_ONLY",
    }
