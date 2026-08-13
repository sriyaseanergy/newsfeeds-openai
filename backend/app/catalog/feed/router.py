from uuid import UUID

from app.api.auth.authorization import require_feed_source_manager
from app.catalog.feed.repository import FeedRepository
from app.catalog.feed.schemas import FeedCreate, FeedResponse, FeedUpdate
from app.catalog.feed.service import (
    FeedDuplicateUrlError,
    FeedNotFoundError,
    FeedService,
    FeedTechnologyDomainNotFoundError,
)
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.employee_database.repository import EmployeeRecord
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/feeds", tags=["Feeds"])


def get_feed_service(db: Session = Depends(get_db)) -> FeedService:
    repository = FeedRepository(db)
    technology_domain_repository = TechnologyDomainRepository(db)
    return FeedService(repository, technology_domain_repository)


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
def create_feed(
    payload: FeedCreate,
    _employee: EmployeeRecord = Depends(require_feed_source_manager),
    service: FeedService = Depends(get_feed_service),
) -> FeedResponse:
    try:
        return service.create(payload)
    except FeedTechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeedDuplicateUrlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[FeedResponse])
def list_feeds(service: FeedService = Depends(get_feed_service)) -> list[FeedResponse]:
    return service.list()


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(feed_id: UUID, service: FeedService = Depends(get_feed_service)) -> FeedResponse:
    try:
        return service.get_by_id(feed_id)
    except FeedNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed(
    feed_id: UUID,
    payload: FeedUpdate,
    _employee: EmployeeRecord = Depends(require_feed_source_manager),
    service: FeedService = Depends(get_feed_service),
) -> FeedResponse:
    try:
        return service.update(feed_id, payload)
    except FeedNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeedTechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeedDuplicateUrlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed(
    feed_id: UUID,
    _employee: EmployeeRecord = Depends(require_feed_source_manager),
    service: FeedService = Depends(get_feed_service),
) -> Response:
    try:
        service.delete(feed_id)
    except FeedNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

