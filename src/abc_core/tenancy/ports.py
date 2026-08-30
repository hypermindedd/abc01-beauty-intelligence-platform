from __future__ import annotations

from typing import Protocol

from abc_core.state.models import SalonSessionState
from .models import Principal, SalonConfig


class AuthProvider(Protocol):
    def authenticate(self, credential: str) -> Principal: ...


class PersistencePort(Protocol):
    def load_session(self, *, tenant_id: str, session_id: str) -> SalonSessionState | None: ...

    def save_session(
        self,
        state: SalonSessionState,
        *,
        expected_revision: int,
    ) -> SalonSessionState: ...


class SalonConfigPort(Protocol):
    def load_config(self, *, tenant_id: str, salon_id: str) -> SalonConfig | None: ...

    def save_config(
        self,
        config: SalonConfig,
        *,
        expected_revision: int,
    ) -> SalonConfig: ...


class SecretProvider(Protocol):
    def get_secret(self, *, tenant_id: str, secret_name: str) -> str: ...
