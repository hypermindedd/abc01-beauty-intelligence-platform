from __future__ import annotations
import pytest
from abc_core.visual_qa import QaDimension, required_dimensions_for_services
from abc_core.visual_qa.service_scope import QaServiceScopeError, resolve_qa_service_scope
from abc_core.service_intelligence.registry import SERVICE_REGISTRY, FORBIDDEN_SERVICE_IDS

@pytest.mark.parametrize('service_id', ['', 'SVC-01-999', 'SVC-03-008', 'CTRL-011', 'CTRL-012', 'CTRL-013', 'CTRL-999'])
def test_unknown_forbidden_or_empty_scope_fails_closed(service_id):
    with pytest.raises(QaServiceScopeError):
        required_dimensions_for_services((service_id,))

@pytest.mark.parametrize('service_id', tuple(SERVICE_REGISTRY))
def test_every_canonical_service_resolves_without_guessing(service_id):
    assert resolve_qa_service_scope((service_id,)).required_dimensions

@pytest.mark.parametrize('service_id', tuple(FORBIDDEN_SERVICE_IDS))
def test_forbidden_ids_never_resolve(service_id):
    with pytest.raises(QaServiceScopeError):
        resolve_qa_service_scope((service_id,))

def test_duplicate_and_empty_scope_rejected():
    for scope in ((), ('SVC-01-001','SVC-01-001')):
        with pytest.raises(QaServiceScopeError):
            resolve_qa_service_scope(scope)

def test_complete_look_inherits_all_component_obligations():
    scope = resolve_qa_service_scope(('CTRL-009',))
    assert {'SVC-01-006','SVC-03-005','SVC-04-007'}.issubset(set(scope.expanded_service_ids))
    assert {QaDimension.HAIR_SHAPE_SOURCE_REALITY, QaDimension.FACE_GEOMETRY_CONTINUITY, QaDimension.HAND_GEOMETRY_CONTINUITY}.issubset(set(scope.required_dimensions))

def test_controlled_service_inherits_exact_component_and_own_obligations():
    for service_id in ('CTRL-001','CTRL-002','CTRL-003','CTRL-004','CTRL-005','CTRL-006','CTRL-008','CTRL-010'):
        definition = SERVICE_REGISTRY[service_id]
        scope = resolve_qa_service_scope((service_id,))
        assert set(definition.component_service_ids).issubset(set(scope.expanded_service_ids))
        for component in definition.component_service_ids:
            assert set(required_dimensions_for_services((component,))).issubset(set(scope.required_dimensions))

def test_smoothing_uses_exact_controlled_profile_without_fabricated_component():
    scope = resolve_qa_service_scope(('CTRL-007',))
    assert scope.expanded_service_ids == ('CTRL-007',)
    assert QaDimension.HAIR_SHAPE_SOURCE_REALITY in scope.required_dimensions

def test_multiservice_requirements_are_additive():
    combined = set(required_dimensions_for_services(('SVC-03-001','SVC-04-001')))
    assert set(required_dimensions_for_services(('SVC-03-001',))).issubset(combined)
    assert set(required_dimensions_for_services(('SVC-04-001',))).issubset(combined)
