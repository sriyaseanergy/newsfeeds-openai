from __future__ import annotations

from app.api.auth.admin_emails import is_feed_source_admin
from app.api.auth.authenticator import EmployeeAuthenticator
from app.api.auth.exceptions import InvalidIdTokenError, MissingEmailClaimError
from app.api.auth.models import AuthenticatedUser
from app.api.auth.schemas import EmployeeResponse, SessionResponse
from app.core.settings import Settings, get_settings
from fastapi import HTTPException, status


def user_to_response(
    user: AuthenticatedUser,
    settings: Settings | None = None,
) -> EmployeeResponse:
    resolved_settings = settings or get_settings()
    return EmployeeResponse(
        emp_no=user.emp_no,
        name=user.name,
        email=user.email,
        designation=user.designation,
        can_manage_feed_sources=is_feed_source_admin(user.email, resolved_settings),
    )


class AuthService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._authenticator = EmployeeAuthenticator(settings=self._settings)

    def create_session(self, id_token: str) -> SessionResponse:
        try:
            user = self._authenticator.authenticate(id_token)
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
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        return SessionResponse(employee=user_to_response(user, self._settings))


def get_auth_service(settings: Settings | None = None) -> AuthService:
    return AuthService(settings=settings)
