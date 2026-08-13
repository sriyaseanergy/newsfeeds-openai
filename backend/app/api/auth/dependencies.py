from __future__ import annotations

from app.api.auth.authenticator import EmployeeAuthenticator
from app.api.auth.exceptions import (
    InactiveEmployeeError,
    InvalidIdTokenError,
    MissingEmailClaimError,
)
from app.core.settings import get_settings
from app.infrastructure.employee_database.repository import (
    EmployeeRecord,
    EmployeeRepository,
)
from app.infrastructure.employee_database.session import get_employee_session_factory
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
) -> EmployeeRecord:
    settings = get_settings()
    try:
        email = EmployeeAuthenticator(settings=settings).resolve_email_from_token(token)
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

    try:
        session_factory = get_employee_session_factory()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    db = session_factory()
    try:
        authenticator = EmployeeAuthenticator(
            EmployeeRepository(db, settings),
            settings=settings,
        )
        return authenticator.lookup_active_employee(email)
    except InactiveEmployeeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    finally:
        db.close()
