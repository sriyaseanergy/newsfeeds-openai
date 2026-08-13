from __future__ import annotations

from app.api.auth.exceptions import InactiveEmployeeError
from app.api.auth.token_validator import AzureAdIdTokenValidator
from app.core.settings import Settings, get_settings
from app.infrastructure.employee_database.repository import (
    EmployeeRecord,
    EmployeeRepository,
)


class EmployeeAuthenticator:
    def __init__(
        self,
        employee_repository: EmployeeRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        resolved_settings = settings or get_settings()
        self._settings = resolved_settings
        self._token_validator = AzureAdIdTokenValidator(resolved_settings)
        self._employee_repository = employee_repository

    def resolve_email_from_token(self, id_token: str) -> str:
        claims = self._token_validator.validate(id_token)
        return self._token_validator.extract_email(claims)

    def lookup_active_employee(self, email: str) -> EmployeeRecord:
        if self._employee_repository is None:
            msg = "Employee repository is required for employee lookup."
            raise ValueError(msg)
        employee = self._employee_repository.find_active_by_email(email)
        if employee is None:
            raise InactiveEmployeeError(
                "No active employee record matches this account."
            )
        return employee

    def authenticate(self, id_token: str) -> EmployeeRecord:
        email = self.resolve_email_from_token(id_token)
        return self.lookup_active_employee(email)
