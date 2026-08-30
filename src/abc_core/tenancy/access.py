from __future__ import annotations

from enum import StrEnum

from .models import Principal, Role


class Permission(StrEnum):
    VIEW_SESSION = "VIEW_SESSION"
    EDIT_SESSION = "EDIT_SESSION"
    SPECIALIST_VALIDATE = "SPECIALIST_VALIDATE"
    VIEW_SALON_CONFIG = "VIEW_SALON_CONFIG"
    EDIT_SALON_CONFIG = "EDIT_SALON_CONFIG"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_SECRETS = "MANAGE_SECRETS"


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.SALON_OWNER: frozenset(Permission),
    Role.SALON_ADMIN: frozenset({
        Permission.VIEW_SESSION,
        Permission.EDIT_SESSION,
        Permission.VIEW_SALON_CONFIG,
        Permission.EDIT_SALON_CONFIG,
        Permission.MANAGE_USERS,
    }),
    Role.SPECIALIST: frozenset({
        Permission.VIEW_SESSION,
        Permission.EDIT_SESSION,
        Permission.SPECIALIST_VALIDATE,
        Permission.VIEW_SALON_CONFIG,
    }),
    Role.CONFIG_EDITOR: frozenset({
        Permission.VIEW_SESSION,
        Permission.VIEW_SALON_CONFIG,
        Permission.EDIT_SALON_CONFIG,
    }),
    Role.READ_ONLY: frozenset({
        Permission.VIEW_SESSION,
        Permission.VIEW_SALON_CONFIG,
    }),
}


class AccessDenied(PermissionError):
    pass


def has_permission(principal: Principal, permission: Permission) -> bool:
    return any(permission in _ROLE_PERMISSIONS[role] for role in principal.roles)


def require_permission(principal: Principal, permission: Permission) -> None:
    if not has_permission(principal, permission):
        raise AccessDenied(
            f"principal {principal.principal_id} lacks permission {permission}"
        )
