from __future__ import annotations

from app.api.auth.models import AuthenticatedUser
from app.api.auth.token_validator import AzureAdIdTokenValidator
from app.catalog.user.schemas import EntraIdentity
from app.catalog.user.service import UserService
from app.core.settings import Settings, get_settings


class EmployeeAuthenticator:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        user_service: UserService,
    ) -> None:
        resolved_settings = settings or get_settings()
        self._settings = resolved_settings
        self._token_validator = AzureAdIdTokenValidator(resolved_settings)
        self._user_service = user_service

    def resolve_email_from_token(self, id_token: str) -> str:
        claims = self._token_validator.validate(id_token)
        return self._token_validator.extract_email(claims)

    def authenticate(self, id_token: str) -> AuthenticatedUser:
        claims = self._token_validator.validate(id_token)
        email = self._token_validator.extract_email(claims)
        name = self._token_validator.extract_name(claims, email)
        oid = self._token_validator.extract_oid(claims)
        tid = self._token_validator.extract_tid(claims)

        self._user_service.record_login(
            EntraIdentity(
                oid=oid,
                tid=tid,
                email=email,
                display_name=name,
            )
        )

        return AuthenticatedUser(
            email=email,
            name=name,
            designation="Employee",
            emp_no=None,
        )
