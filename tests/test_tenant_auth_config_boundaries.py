import pytest
from pydantic import ValidationError

from abc_core.state.models import SalonSessionState
from abc_core.tenancy import (
    AccessDenied,
    InfrastructureCapability,
    InfrastructureStatus,
    InfrastructureTruth,
    InfrastructureUnavailable,
    Permission,
    Principal,
    Role,
    SalonConfig,
    TenantContext,
    TenantScopeViolation,
    require_config_scope,
    require_permission,
    require_session_scope,
)


def principal(role: Role, tenant_id: str = "tenant-1") -> Principal:
    return Principal(principal_id=f"p-{role}", tenant_id=tenant_id, roles=(role,))


def context(role: Role = Role.SPECIALIST) -> TenantContext:
    return TenantContext(
        tenant_id="tenant-1",
        salon_id="salon-1",
        principal=principal(role),
    )


def test_tenant_context_rejects_cross_tenant_principal():
    with pytest.raises(ValidationError):
        TenantContext(
            tenant_id="tenant-a",
            salon_id="salon-1",
            principal=principal(Role.SPECIALIST, tenant_id="tenant-b"),
        )


def test_read_only_cannot_edit_session_or_config():
    p = principal(Role.READ_ONLY)
    require_permission(p, Permission.VIEW_SESSION)
    require_permission(p, Permission.VIEW_SALON_CONFIG)
    with pytest.raises(AccessDenied):
        require_permission(p, Permission.EDIT_SESSION)
    with pytest.raises(AccessDenied):
        require_permission(p, Permission.EDIT_SALON_CONFIG)


def test_specialist_validation_permission_is_not_granted_to_admin_or_config_editor():
    require_permission(principal(Role.SPECIALIST), Permission.SPECIALIST_VALIDATE)
    with pytest.raises(AccessDenied):
        require_permission(principal(Role.SALON_ADMIN), Permission.SPECIALIST_VALIDATE)
    with pytest.raises(AccessDenied):
        require_permission(principal(Role.CONFIG_EDITOR), Permission.SPECIALIST_VALIDATE)


def test_only_owner_has_secret_management_permission():
    require_permission(principal(Role.SALON_OWNER), Permission.MANAGE_SECRETS)
    for role in (Role.SALON_ADMIN, Role.SPECIALIST, Role.CONFIG_EDITOR, Role.READ_ONLY):
        with pytest.raises(AccessDenied):
            require_permission(principal(role), Permission.MANAGE_SECRETS)


def test_session_scope_fails_closed_across_tenants():
    state = SalonSessionState(tenant_id="tenant-2", session_id="session-1")
    with pytest.raises(TenantScopeViolation):
        require_session_scope(context(), state)


def test_salon_config_scope_requires_tenant_and_salon_match():
    ctx = context()
    correct = SalonConfig(
        tenant_id="tenant-1",
        salon_id="salon-1",
        display_name="ABC Salon",
    )
    require_config_scope(ctx, correct)

    wrong_salon = correct.model_copy(update={"salon_id": "salon-2"})
    with pytest.raises(TenantScopeViolation):
        require_config_scope(ctx, wrong_salon)


def test_salon_config_rejects_duplicate_controlled_values():
    with pytest.raises(ValidationError):
        SalonConfig(
            tenant_id="tenant-1",
            salon_id="salon-1",
            display_name="ABC Salon",
            enabled_service_ids=("SVC-01-001", "SVC-01-001"),
        )


def test_default_infrastructure_truth_is_interface_only_not_production_verified():
    truth = InfrastructureTruth()
    assert truth.public() == {
        "AUTH": "INTERFACE_ONLY",
        "PERSISTENCE": "INTERFACE_ONLY",
        "SECRETS": "INTERFACE_ONLY",
        "SALON_CONFIG": "INTERFACE_ONLY",
    }
    for capability in InfrastructureCapability:
        assert truth.status(capability) is InfrastructureStatus.INTERFACE_ONLY
        assert truth.is_verified(capability) is False
        with pytest.raises(InfrastructureUnavailable):
            truth.require_verified(capability)


def test_verified_capability_must_be_explicit_not_inferred_from_interface_presence():
    truth = InfrastructureTruth(
        statuses={InfrastructureCapability.SALON_CONFIG: InfrastructureStatus.VERIFIED}
    )
    assert truth.is_verified(InfrastructureCapability.SALON_CONFIG) is True
    assert truth.status(InfrastructureCapability.AUTH) is InfrastructureStatus.UNAVAILABLE
