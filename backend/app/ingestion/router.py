from app.ingestion.schemas import IngestionRunRequest, IngestionRunResponse
from app.ingestion.service import IngestionService
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


def get_ingestion_service(db: Session = Depends(get_db)) -> IngestionService:
    return IngestionService(db=db)


@router.post("/run", response_model=IngestionRunResponse, status_code=status.HTTP_200_OK)
def run_ingestion(
    payload: IngestionRunRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestionRunResponse:
    results = service.ingest_scheduled_domains(payload.schedule)
    return IngestionRunResponse(results=list(results))

