from uuid import UUID

from app.api.auth.authorization import require_feed_source_manager
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.catalog.technology_domain.schemas import (
    TechnologyDomainCreate,
    TechnologyDomainResponse,
    TechnologyDomainUpdate,
)
from app.catalog.technology_domain.service import (
    TechnologyDomainDuplicateNameError,
    TechnologyDomainNotFoundError,
    TechnologyDomainService,
)
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/technology-domains", tags=["Technology Domains"])


def get_technology_domain_service(
    db: Session = Depends(get_db),
) -> TechnologyDomainService:
    repository = TechnologyDomainRepository(db)
    return TechnologyDomainService(repository)


@router.post(
    "",
    response_model=TechnologyDomainResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technology_domain(
    payload: TechnologyDomainCreate,
    _employee=Depends(require_feed_source_manager),
    service: TechnologyDomainService = Depends(get_technology_domain_service),
) -> TechnologyDomainResponse:
    try:
        return service.create(payload)
    except TechnologyDomainDuplicateNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[TechnologyDomainResponse])
def list_technology_domains(
    service: TechnologyDomainService = Depends(get_technology_domain_service),
) -> list[TechnologyDomainResponse]:
    return service.list()


@router.get("/{domain_id}", response_model=TechnologyDomainResponse)
def get_technology_domain(
    domain_id: UUID,
    service: TechnologyDomainService = Depends(get_technology_domain_service),
) -> TechnologyDomainResponse:
    try:
        return service.get_by_id(domain_id)
    except TechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{domain_id}", response_model=TechnologyDomainResponse)
def update_technology_domain(
    domain_id: UUID,
    payload: TechnologyDomainUpdate,
    _employee=Depends(require_feed_source_manager),
    service: TechnologyDomainService = Depends(get_technology_domain_service),
) -> TechnologyDomainResponse:
    try:
        return service.update(domain_id, payload)
    except TechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TechnologyDomainDuplicateNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_technology_domain(
    domain_id: UUID,
    _employee=Depends(require_feed_source_manager),
    service: TechnologyDomainService = Depends(get_technology_domain_service),
) -> Response:
    try:
        service.delete(domain_id)
    except TechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)

