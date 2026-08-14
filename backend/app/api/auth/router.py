from app.api.auth.dependencies import get_current_employee
from app.api.auth.schemas import EmployeeResponse, SessionRequest, SessionResponse
from app.api.auth.service import AuthService, employee_to_response, get_auth_service
from app.infrastructure.employee_database.repository import EmployeeRecord
from app.infrastructure.employee_database.session import get_employee_db
from app.infrastructure.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_auth_service(db: Session = Depends(get_employee_db)) -> AuthService:
    try:
        return get_auth_service(db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/me", response_model=EmployeeResponse)
def get_authenticated_employee(
    employee: EmployeeRecord = Depends(get_current_employee),
) -> EmployeeResponse:
    return employee_to_response(employee)


@router.post("/session", response_model=SessionResponse)
def create_session(
    payload: SessionRequest,
    service: AuthService = Depends(_get_auth_service),
) -> SessionResponse:
    try:
        return service.create_session(payload.id_token)
    except SQLAlchemyError as exc:
        logger.exception("MyWork employee lookup failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Employee database is unavailable.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Session creation failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        ) from exc
