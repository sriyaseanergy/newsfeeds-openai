from app.api.health.schemas import HealthResponse
from app.api.health.service import HealthService
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    return HealthService.get_health(db)
