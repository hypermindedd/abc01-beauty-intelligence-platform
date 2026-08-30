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
from .runtime import InfrastructureTruth

__all__ = [
    "AccessDenied",
    "AuthProvider",
    "InfrastructureCapability",
    "InfrastructureStatus",
    "InfrastructureTruth",
    "Permission",
    "PersistencePort",
    "Principal",
    "Role",
    "SalonConfig",
    "SalonConfigPort",
    "SecretProvider",
    "TenantContext",
    "require_permission",
]
