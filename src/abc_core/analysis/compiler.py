from __future__ import annotations

from abc_core.state.models import AnalysisState, EvidenceItem

from .contracts import BeautyAnalysisBundle


def compile_analysis_state(bundle: BeautyAnalysisBundle) -> AnalysisState:
    """Project one validated analysis bundle into canonical session truth."""
    return AnalysisState(
        analysis_id=bundle.analysis_id,
        summary=bundle.shared_summary,
        shared_summary=bundle.shared_summary,
        specialist_summary=bundle.specialist_summary,
        strategy_summary=bundle.strategy.summary,
        capture_plan_ids=(bundle.capture_assessment.plan_id,),
        capture_sufficient=bundle.capture_assessment.sufficient,
        finding_ids=tuple(item.finding_id for item in bundle.findings),
        reviewed_by_specialist=bundle.specialist_reviewed,
        reviewer_actor_id=bundle.specialist_reviewer_id,
    )


def compile_evidence_items(bundle: BeautyAnalysisBundle) -> tuple[EvidenceItem, ...]:
    """Compile analysis findings to canonical evidence without changing provenance class."""
    return tuple(
        EvidenceItem(
            evidence_id=f"EV-{finding.finding_id}",
            evidence_class=finding.evidence_class,
            statement=finding.statement,
        )
        for finding in bundle.findings
    )
