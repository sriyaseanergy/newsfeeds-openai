from __future__ import annotations

from app.api.auth.authenticator import EmployeeAuthenticator
from app.api.auth.exceptions import (
    InvalidIdTokenError,
    MissingEmailClaimError,
    MissingOidClaimError,
    MissingTidClaimError,
)
from app.api.auth.models import AuthenticatedUser
from app.api.auth.service import AuthService
from app.catalog.user.model import User
from app.catalog.user.repository import UserRepository
from app.catalog.user.service import UserConflictError, UserService
from app.core.settings import get_settings
from app.infrastructure.database.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(user_service=user_service)


def require_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication.",
        )
    return credentials.credentials


def _build_authenticator(user_service: UserService) -> EmployeeAuthenticator:
    settings = get_settings()
    return EmployeeAuthenticator(settings=settings, user_service=user_service)


def _map_authentication_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidIdTokenError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Azure AD ID token.",
        )
    if isinstance(exc, (MissingEmailClaimError, MissingOidClaimError, MissingTidClaimError)):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    if isinstance(exc, UserConflictError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        )
    if isinstance(exc, ValueError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    raise exc


def get_current_employee(
    token: str = Depends(require_bearer_token),
    user_service: UserService = Depends(get_user_service),
) -> AuthenticatedUser:
    authenticator = _build_authenticator(user_service)
    try:
        return authenticator.authenticate(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_authentication_errors(exc) from exc


def get_current_user(
    token: str = Depends(require_bearer_token),
    user_service: UserService = Depends(get_user_service),
) -> User:
    authenticator = _build_authenticator(user_service)
    try:
        return authenticator.get_catalog_user(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_authentication_errors(exc) from exc
