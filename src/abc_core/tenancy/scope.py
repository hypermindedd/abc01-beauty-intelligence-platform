from __future__ import annotations

from abc_core.state.models import SalonSessionState
from .models import SalonConfig, TenantContext


class TenantScopeViolation(PermissionError):
    pass


def require_session_scope(context: TenantContext, state: SalonSessionState) -> None:
    if context.tenant_id != state.tenant_id:
        raise TenantScopeViolation("session tenant does not match tenant context")


def require_config_scope(context: TenantContext, config: SalonConfig) -> None:
    if context.tenant_id != config.tenant_id:
        raise TenantScopeViolation("config tenant does not match tenant context")
    if context.salon_id != config.salon_id:
        raise TenantScopeViolation("config salon does not match tenant context")
