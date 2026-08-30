from __future__ import annotations

from dataclasses import dataclass

from .contracts import BeautyAnalysisBundle, CaptureInput, CapturePlan, Domain
from .engine import AnalysisContractViolation, CrossDomainAnalysisEngine
from .ports import AnalysisExtractionRequest, MultimodalAnalysisExtractor


@dataclass(frozen=True)
class GovernedAnalysisRuntime:
    engine: CrossDomainAnalysisEngine
    extractor: MultimodalAnalysisExtractor

    def run(
        self,
        *,
        tenant_id: str,
        session_id: str,
        domain: Domain,
        service_ids: tuple[str, ...],
        plan: CapturePlan,
        capture_inputs: tuple[CaptureInput, ...],
        known_evidence_ids: tuple[str, ...] = (),
    ) -> BeautyAnalysisBundle:
        assessment = self.engine.assess_capture(plan, capture_inputs)
        if not assessment.sufficient:
            raise AnalysisContractViolation(
                "multimodal extraction blocked because required capture is insufficient"
            )

        request = AnalysisExtractionRequest(
            tenant_id=tenant_id,
            session_id=session_id,
            domain=domain,
            service_ids=service_ids,
            capture_inputs=capture_inputs,
            known_evidence_ids=known_evidence_ids,
        )
        raw = self.extractor.extract(request)

        known_asset_ids = {item.asset_id for item in capture_inputs}
        self.engine.validate_findings(
            raw.findings,
            known_asset_ids=known_asset_ids,
            known_evidence_ids=set(known_evidence_ids),
        )
        self.engine.require_analysis_ready(assessment, raw.findings)

        return BeautyAnalysisBundle(
            analysis_id=f"AN-{session_id}-{domain.value}",
            capture_assessment=assessment,
            findings=raw.findings,
            shared_summary=raw.shared_summary,
            specialist_summary=raw.specialist_summary,
            strategy=raw.strategy,
        )
