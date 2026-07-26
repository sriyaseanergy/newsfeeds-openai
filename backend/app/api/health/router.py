from app.api.health.schemas import HealthResponse
from app.api.health.service import HealthService
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthService.get_health()
