from __future__ import annotations

from app.api.auth.authenticator import EmployeeAuthenticator
from app.api.auth.exceptions import InvalidIdTokenError, MissingEmailClaimError
from app.api.auth.models import AuthenticatedUser
from app.core.settings import get_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)


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
) -> AuthenticatedUser:
    settings = get_settings()
    authenticator = EmployeeAuthenticator(settings=settings)
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
    except MissingEmailClaimError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
