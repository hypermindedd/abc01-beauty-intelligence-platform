from __future__ import annotations

from abc_core.state import RecommendationComponentState, RecommendationOption, RecommendationSet

from .contracts import RankedDirection, RecommendationCompilation


def _component_state(component) -> RecommendationComponentState:
    return RecommendationComponentState(
        component_id=component.component_id,
        domain=str(component.domain),
        label=component.label,
        service_ids=component.service_ids,
        rationale=component.rationale,
        evidence_ids=component.evidence_ids,
    )


def _option(direction: RankedDirection) -> RecommendationOption:
    return RecommendationOption(
        option_id=direction.option_id,
        title=direction.title,
        role=direction.role,
        is_explore=direction.is_explore,
        components=tuple(_component_state(component) for component in direction.components),
        intensity=str(direction.intensity),
        maintenance=direction.maintenance,
        tradeoff=direction.tradeoff,
        source_constraints=direction.source_constraints,
        preview_ready=direction.preview_ready,
    )


def compile_recommendation_set(
    compilation: RecommendationCompilation,
    *,
    recommendation_set_id: str,
) -> RecommendationSet:
    """Losslessly project governed ranked directions into canonical session truth.

    This compiler does not rank, invent, repair or pad options. The upstream engine
    must already have applied analysis review, source-reality filtering, diversity,
    role assignment and explicit Explore rules.
    """
    return RecommendationSet(
        recommendation_set_id=recommendation_set_id,
        core_options=tuple(_option(direction) for direction in compilation.core),
        explore_options=tuple(_option(direction) for direction in compilation.explore),
        rules_applied=compilation.rules_applied,
    )
