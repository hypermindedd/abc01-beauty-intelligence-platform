from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Role(StrEnum):
    SALON_OWNER = "SALON_OWNER"
    SALON_ADMIN = "SALON_ADMIN"
    SPECIALIST = "SPECIALIST"
    CONFIG_EDITOR = "CONFIG_EDITOR"
    READ_ONLY = "READ_ONLY"


class InfrastructureCapability(StrEnum):
    AUTH = "AUTH"
    PERSISTENCE = "PERSISTENCE"
    SECRETS = "SECRETS"
    SALON_CONFIG = "SALON_CONFIG"


class InfrastructureStatus(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    INTERFACE_ONLY = "INTERFACE_ONLY"
    CONFIGURED = "CONFIGURED"
    VERIFIED = "VERIFIED"


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    principal_id: str
    tenant_id: str
    roles: tuple[Role, ...]

    @field_validator("roles")
    @classmethod
    def roles_must_not_be_empty(cls, value: tuple[Role, ...]) -> tuple[Role, ...]:
        if not value:
            raise ValueError("principal must have at least one role")
        if len(set(value)) != len(value):
            raise ValueError("principal roles must be unique")
        return value


class TenantContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    salon_id: str
    principal: Principal

    @field_validator("principal")
    @classmethod
    def principal_must_match_tenant(cls, principal: Principal, info):
        tenant_id = info.data.get("tenant_id")
        if tenant_id and principal.tenant_id != tenant_id:
            raise ValueError("principal tenant does not match tenant context")
        return principal


class SalonConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    salon_id: str
    revision: int = Field(default=0, ge=0)
    display_name: str
    locale: str = "fa-IR"
    enabled_service_ids: tuple[str, ...] = ()
    enabled_feature_ids: tuple[str, ...] = ()
    specialist_ids: tuple[str, ...] = ()
    price_display_enabled: bool = False
    booking_integration_enabled: bool = False

    @field_validator("enabled_service_ids", "enabled_feature_ids", "specialist_ids")
    @classmethod
    def values_must_be_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("configuration values must be unique")
        return value
