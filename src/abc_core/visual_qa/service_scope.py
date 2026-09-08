"""Exact, additive QA obligations from the governed service registry."""
from __future__ import annotations
from dataclasses import dataclass
from abc_core.service_intelligence.registry import SERVICE_REGISTRY, FORBIDDEN_SERVICE_IDS
from .contracts import QaDimension

_BASELINE = (
    QaDimension.REQUESTED_CHANGE_FIDELITY,
    QaDimension.UNRELATED_REGION_INTEGRITY,
    QaDimension.DOMAIN_SOURCE_REALITY,
)
_HAIR = (QaDimension.IDENTITY_CONTINUITY, QaDimension.HAIR_SHAPE_SOURCE_REALITY)
_FACE = (QaDimension.IDENTITY_CONTINUITY, QaDimension.FACE_GEOMETRY_CONTINUITY)
_GROOM = _FACE + (QaDimension.HAIR_SHAPE_SOURCE_REALITY, QaDimension.FACIAL_HAIR_SOURCE_REALITY)
_NAILS = (QaDimension.HAND_GEOMETRY_CONTINUITY,)
_FAMILY_OBLIGATIONS = {
    'SVC-01': _HAIR, 'SVC-02': _HAIR, 'SVC-03': _FACE,
    'SVC-04': _NAILS, 'SVC-05': _GROOM,
}
# These are QA profiles, not new service definitions or execution permissions.
_CONTROLLED_OBLIGATIONS = {
    'CTRL-001': _HAIR, 'CTRL-002': _FACE, 'CTRL-003': _NAILS,
    'CTRL-004': _GROOM, 'CTRL-005': _HAIR, 'CTRL-006': _HAIR,
    'CTRL-007': _HAIR, 'CTRL-008': _FACE,
    'CTRL-009': _HAIR + _FACE + _NAILS, 'CTRL-010': _NAILS,
}

class QaServiceScopeError(ValueError):
    pass

@dataclass(frozen=True)
class ResolvedQaScope:
    requested_service_ids: tuple[str, ...]
    expanded_service_ids: tuple[str, ...]
    required_dimensions: tuple[QaDimension, ...]


def resolve_qa_service_scope(service_ids: tuple[str, ...]) -> ResolvedQaScope:
    if not service_ids or len(set(service_ids)) != len(service_ids):
        raise QaServiceScopeError('service scope must be nonempty and unique')
    requested = tuple(sorted(service_ids))
    expanded: list[str] = []
    visited: set[str] = set()
    active: set[str] = set()
    required = list(_BASELINE)

    def visit(service_id: str) -> None:
        if service_id in FORBIDDEN_SERVICE_IDS or service_id not in SERVICE_REGISTRY:
            raise QaServiceScopeError(f'unknown or forbidden service: {service_id}')
        if service_id in active:
            raise QaServiceScopeError('controlled-service component cycle')
        if service_id in visited:
            return
        definition = SERVICE_REGISTRY[service_id]
        active.add(service_id)
        own = (_CONTROLLED_OBLIGATIONS.get(service_id) if definition.family == 'CONTROLLED'
               else _FAMILY_OBLIGATIONS.get(definition.family))
        if own is None:
            raise QaServiceScopeError(f'QA obligations unresolved: {service_id}')
        required.extend(own)
        for component_id in definition.component_service_ids:
            visit(component_id)
        active.remove(service_id)
        visited.add(service_id)
        expanded.append(service_id)

    for service_id in requested:
        visit(service_id)
    return ResolvedQaScope(requested, tuple(sorted(expanded)), tuple(dict.fromkeys(required)))


def required_dimensions_for_services(service_ids: tuple[str, ...]) -> tuple[QaDimension, ...]:
    return resolve_qa_service_scope(service_ids).required_dimensions
