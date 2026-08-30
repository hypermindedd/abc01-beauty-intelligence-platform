"""Tenant, role, salon configuration and infrastructure-boundary contracts."""

from .access import AccessDenied, Permission, require_permission
from .models import (
    InfrastructureCapability,
    InfrastructureStatus,
    Principal,
    Role,
    SalonConfig,
    TenantContext,
)
from .ports import AuthProvider, PersistencePort, SalonConfigPort, SecretProvider
from .runtime import INFRASTRUCTURE, InfrastructureTruth, InfrastructureUnavailable
from .scope import TenantScopeViolation, require_config_scope, require_session_scope

__all__ = [
    "AccessDenied",
    "AuthProvider",
    "INFRASTRUCTURE",
    "InfrastructureCapability",
    "InfrastructureStatus",
    "InfrastructureTruth",
    "InfrastructureUnavailable",
    "Permission",
    "PersistencePort",
    "Principal",
    "Role",
    "SalonConfig",
    "SalonConfigPort",
    "SecretProvider",
    "TenantContext",
    "TenantScopeViolation",
    "require_config_scope",
    "require_permission",
    "require_session_scope",
]
