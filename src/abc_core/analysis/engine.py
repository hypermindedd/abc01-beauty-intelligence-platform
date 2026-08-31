from __future__ import annotations

from dataclasses import dataclass

from abc_core.state.enums import EvidenceClass

from .contracts import (
    AnalysisFinding,
    BeautyAnalysisBundle,
    CaptureAssessment,
    CaptureInput,
    CapturePlan,
    FindingVisibility,
    ImageQuality,
)


class AnalysisContractViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class CrossDomainAnalysisEngine:
    """Deterministic governance layer around multimodal analysis output.

    This component does not infer beauty facts itself. It validates capture
    sufficiency, evidence provenance and audience projections around findings
    produced by an approved analyzer/provider.
    """

    def assess_capture(
        self,
        plan: CapturePlan,
        inputs: tuple[CaptureInput, ...],
    ) -> CaptureAssessment:
        satisfied: list[str] = []
        missing: list[str] = []
        limited: list[str] = []

        for requirement in plan.requirements:
            matching = [item for item in inputs if item.view is requirement.view]
            strong_enough = [
                item for item in matching
                if item.quality in {ImageQuality.USABLE, ImageQuality.STRONG}
            ]
            limited_only = [item for item in matching if item.quality is ImageQuality.LIMITED]

            if len(strong_enough) >= requirement.min_count:
                satisfied.append(requirement.requirement_id)
                continue

            if limited_only:
                limited.append(requirement.requirement_id)
            if requirement.required:
                missing.append(requirement.requirement_id)

        sufficient = not missing
        note = (
            "required capture contract satisfied"
            if sufficient
            else "required capture contract incomplete; analysis must fail closed"
        )
        return CaptureAssessment(
            plan_id=plan.plan_id,
            sufficient=sufficient,
            satisfied_requirement_ids=tuple(satisfied),
            missing_requirement_ids=tuple(missing),
            limited_requirement_ids=tuple(limited),
            note=note,
        )

    def validate_findings(
        self,
        findings: tuple[AnalysisFinding, ...],
        *,
        known_asset_ids: set[str],
        known_evidence_ids: set[str],
    ) -> None:
        ids = [finding.finding_id for finding in findings]
        if len(ids) != len(set(ids)):
            raise AnalysisContractViolation("duplicate analysis finding id")

        for finding in findings:
            unknown_assets = set(finding.source_asset_ids) - known_asset_ids
            unknown_evidence = set(finding.source_evidence_ids) - known_evidence_ids
            if unknown_assets:
                raise AnalysisContractViolation(
                    f"finding {finding.finding_id} references unknown assets"
                )
            if unknown_evidence:
                raise AnalysisContractViolation(
                    f"finding {finding.finding_id} references unknown evidence"
                )
            if finding.evidence_class is EvidenceClass.INFERRED:
                if not finding.source_asset_ids and not finding.source_evidence_ids:
                    raise AnalysisContractViolation(
                        f"inferred finding {finding.finding_id} requires provenance"
                    )
            if finding.evidence_class is EvidenceClass.KNOWN:
                if not finding.source_evidence_ids:
                    raise AnalysisContractViolation(
                        f"known finding {finding.finding_id} requires governed evidence"
                    )

    def require_analysis_ready(
        self,
        assessment: CaptureAssessment,
        findings: tuple[AnalysisFinding, ...],
    ) -> None:
        if not assessment.sufficient:
            raise AnalysisContractViolation(
                "analysis cannot be finalized from insufficient required capture"
            )
        if not findings:
            raise AnalysisContractViolation(
                "analysis cannot be finalized without evidence-grounded findings"
            )

    def shared_findings(self, bundle: BeautyAnalysisBundle) -> tuple[AnalysisFinding, ...]:
        return tuple(
            finding
            for finding in bundle.findings
            if finding.visibility is FindingVisibility.SHARED
        )

    def specialist_findings(self, bundle: BeautyAnalysisBundle) -> tuple[AnalysisFinding, ...]:
        return bundle.findings

    def mark_specialist_reviewed(
        self,
        bundle: BeautyAnalysisBundle,
        *,
        specialist_actor_id: str,
    ) -> BeautyAnalysisBundle:
        self.require_analysis_ready(bundle.capture_assessment, bundle.findings)
        return bundle.model_copy(
            update={
                "specialist_reviewed": True,
                "specialist_reviewer_id": specialist_actor_id,
            }
        )
