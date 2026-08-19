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


def get_current_employee(
    token: str = Depends(require_bearer_token),
    user_service: UserService = Depends(get_user_service),
) -> AuthenticatedUser:
    settings = get_settings()
    authenticator = EmployeeAuthenticator(settings=settings, user_service=user_service)
    try:
        return authenticator.authenticate(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Azure AD ID token.",
        ) from exc
    except (
        MissingEmailClaimError,
        MissingOidClaimError,
        MissingTidClaimError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except UserConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc
