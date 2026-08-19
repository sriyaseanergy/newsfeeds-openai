from app.api.auth.dependencies import get_auth_service, get_current_employee
from app.api.auth.schemas import EmployeeResponse, SessionRequest, SessionResponse
from app.api.auth.service import AuthService, user_to_response
from app.core.settings import get_settings
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=EmployeeResponse)
def get_authenticated_employee(
    employee=Depends(get_current_employee),
) -> EmployeeResponse:
    return user_to_response(employee, get_settings())


@router.post("/session", response_model=SessionResponse)
def create_session(
    payload: SessionRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionResponse:
    try:
        return auth_service.create_session(payload.id_token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        ) from exc
