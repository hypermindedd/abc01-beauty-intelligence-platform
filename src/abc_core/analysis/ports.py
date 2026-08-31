from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict

from .contracts import AnalysisFinding, AnalysisStrategy, CaptureInput, Domain


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AnalysisExtractionRequest(FrozenModel):
    tenant_id: str
    session_id: str
    domain: Domain
    service_ids: tuple[str, ...]
    capture_inputs: tuple[CaptureInput, ...]
    known_evidence_ids: tuple[str, ...] = ()


class AnalysisExtractionResult(FrozenModel):
    findings: tuple[AnalysisFinding, ...]
    shared_summary: str
    specialist_summary: str
    strategy: AnalysisStrategy


class MultimodalAnalysisExtractor(Protocol):
    """Untrusted analyzer/provider boundary.

    Implementations may use a model or deterministic analyzer, but returned
    claims do not enter canonical analysis until the governance engine validates
    capture sufficiency and provenance.
    """

    def extract(self, request: AnalysisExtractionRequest) -> AnalysisExtractionResult: ...
