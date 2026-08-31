"""Governed recommendation runtime for R02.6."""

from .compiler import compile_recommendation_set
from .contracts import (
    CandidateDirection,
    ChangeIntensity,
    DirectionComponent,
    EvaluatedDirection,
    RankedDirection,
    RealityRequirement,
    RecommendationCompilation,
)
from .engine import RecommendationContractViolation, RecommendationEngine

__all__ = [
    "CandidateDirection",
    "ChangeIntensity",
    "DirectionComponent",
    "EvaluatedDirection",
    "RankedDirection",
    "RealityRequirement",
    "RecommendationCompilation",
    "RecommendationContractViolation",
    "RecommendationEngine",
    "compile_recommendation_set",
]
