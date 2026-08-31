from __future__ import annotations

from abc_core.analysis.contracts import BeautyAnalysisBundle
from abc_core.state.enums import RecommendationRole

from .contracts import CandidateDirection, EvaluatedDirection, RankedDirection, RecommendationCompilation


class RecommendationContractViolation(RuntimeError):
    pass


class RecommendationEngine:
    max_core = 3
    max_explore = 3

    def evaluate_candidate(self, candidate: CandidateDirection, *, source_reality: dict[str, str]) -> EvaluatedDirection:
        reasons: list[str] = []
        for component in candidate.components:
            if not component.service_ids:
                reasons.append(f"{component.component_id}:missing_service_owner")
            for requirement in component.reality_requirements:
                actual = source_reality.get(requirement.key)
                if actual is None:
                    reasons.append(f"{component.component_id}:unknown_source_reality:{requirement.key}")
                elif actual not in requirement.allowed_values:
                    reasons.append(f"{component.component_id}:source_reality_mismatch:{requirement.key}={actual}")
        return EvaluatedDirection(candidate=candidate, valid=not reasons, rejection_reasons=tuple(reasons))

    def compile(
        self,
        *,
        analysis: BeautyAnalysisBundle,
        candidates: tuple[CandidateDirection, ...],
        source_reality: dict[str, str],
        explicit_explore_requested: bool = False,
        fixed_choice: bool = False,
    ) -> RecommendationCompilation:
        if not analysis.specialist_reviewed:
            raise RecommendationContractViolation("ranked recommendations require specialist-reviewed analysis")
        if not analysis.capture_assessment.sufficient:
            raise RecommendationContractViolation("ranked recommendations require sufficient governed capture")

        evaluations = tuple(self.evaluate_candidate(candidate, source_reality=source_reality) for candidate in candidates)
        valid = [evaluation.candidate for evaluation in evaluations if evaluation.valid]
        rejected = tuple(evaluation for evaluation in evaluations if not evaluation.valid)

        distinct: list[CandidateDirection] = []
        seen_signatures: set[tuple[str, ...]] = set()
        for candidate in valid:
            signature = candidate.structural_signature
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            distinct.append(candidate)

        core_candidates = distinct[: self.max_core]
        roles = (RecommendationRole.BEST_FIT, RecommendationRole.ALTERNATIVE, RecommendationRole.BOLDER)
        core = tuple(self._ranked(candidate, role=roles[index], is_explore=False) for index, candidate in enumerate(core_candidates))

        explore: tuple[RankedDirection, ...] = ()
        if explicit_explore_requested and not fixed_choice:
            explore_candidates = distinct[self.max_core : self.max_core + self.max_explore]
            explore = tuple(self._ranked(candidate, role=None, is_explore=True) for candidate in explore_candidates)

        return RecommendationCompilation(
            core=core,
            explore=explore,
            rejected=rejected,
            rules_applied=(
                "ANALYSIS_REVIEW_REQUIRED",
                "FILTER_BEFORE_RANK",
                "NO_FILLER",
                "SOURCE_REALITY_CONSTRAINT",
                "CORE_1_TO_3_VALID_DIRECTIONS",
                "EXPLORE_EXPLICIT_ONLY",
                "FIXED_CHOICE_NO_AUTO_EXPANSION",
            ),
        )

    @staticmethod
    def _ranked(candidate: CandidateDirection, *, role: RecommendationRole | None, is_explore: bool) -> RankedDirection:
        return RankedDirection(
            option_id=candidate.option_id,
            title=candidate.title,
            role=role,
            is_explore=is_explore,
            components=candidate.components,
            intensity=candidate.intensity,
            maintenance=candidate.maintenance,
            tradeoff=candidate.tradeoff,
            source_constraints=candidate.source_constraints,
            preview_ready=candidate.preview_ready,
        )
