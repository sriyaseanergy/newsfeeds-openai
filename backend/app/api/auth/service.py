from __future__ import annotations

from app.api.auth.authenticator import EmployeeAuthenticator
from app.api.auth.exceptions import (
    InactiveEmployeeError,
    InvalidIdTokenError,
    MissingEmailClaimError,
)
from app.api.auth.schemas import EmployeeResponse, SessionResponse
from app.core.settings import Settings, get_settings
from app.infrastructure.employee_database.repository import EmployeeRepository
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def employee_to_response(employee) -> EmployeeResponse:
    return EmployeeResponse(
        emp_no=employee.emp_no,
        name=employee.name,
        email=employee.email,
        designation=employee.designation,
    )


class AuthService:
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        settings: Settings | None = None,
    ) -> None:
        self._authenticator = EmployeeAuthenticator(
            employee_repository,
            settings=settings,
        )

    def create_session(self, id_token: str) -> SessionResponse:
        try:
            employee = self._authenticator.authenticate(id_token)
        except InvalidIdTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Azure AD ID token.",
            ) from exc
        except MissingEmailClaimError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc
        except InactiveEmployeeError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

        return SessionResponse(employee=employee_to_response(employee))


def get_auth_service(
    employee_db: Session,
    settings: Settings | None = None,
) -> AuthService:
    resolved_settings = settings or get_settings()
    employee_repository = EmployeeRepository(employee_db, resolved_settings)
    return AuthService(employee_repository, settings=resolved_settings)
