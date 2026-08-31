from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abc_core.analysis.contracts import Domain
from abc_core.state.enums import RecommendationRole


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ChangeIntensity(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RealityRequirement(FrozenModel):
    key: str
    allowed_values: tuple[str, ...]


class DirectionComponent(FrozenModel):
    component_id: str
    domain: Domain
    label: str
    service_ids: tuple[str, ...]
    rationale: str
    evidence_ids: tuple[str, ...] = ()
    reality_requirements: tuple[RealityRequirement, ...] = ()
    compatibility_tags: tuple[str, ...] = ()


class CandidateDirection(FrozenModel):
    option_id: str
    title: str
    components: tuple[DirectionComponent, ...]
    intensity: ChangeIntensity
    maintenance: str
    tradeoff: str
    source_constraints: tuple[str, ...] = ()
    preview_ready: bool = True

    @model_validator(mode="after")
    def require_composed_direction(self):
        if not self.components:
            raise ValueError("direction requires at least one component")
        if not self.title.strip():
            raise ValueError("direction title is required")
        return self

    @property
    def structural_signature(self) -> tuple[str, ...]:
        return tuple(sorted(component.component_id for component in self.components))


class EvaluatedDirection(FrozenModel):
    candidate: CandidateDirection
    valid: bool
    rejection_reasons: tuple[str, ...] = ()


class RankedDirection(FrozenModel):
    option_id: str
    title: str
    role: RecommendationRole | None = None
    is_explore: bool = False
    components: tuple[DirectionComponent, ...]
    intensity: ChangeIntensity
    maintenance: str
    tradeoff: str
    source_constraints: tuple[str, ...] = ()
    preview_ready: bool = True


class RecommendationCompilation(FrozenModel):
    core: tuple[RankedDirection, ...]
    explore: tuple[RankedDirection, ...] = ()
    rejected: tuple[EvaluatedDirection, ...] = ()
    rules_applied: tuple[str, ...] = Field(default_factory=tuple)
