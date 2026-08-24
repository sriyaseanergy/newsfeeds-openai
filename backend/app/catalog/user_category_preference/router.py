from uuid import UUID

from app.api.auth.dependencies import get_current_user
from app.catalog.feed.repository import FeedRepository
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.catalog.user.model import User
from app.catalog.user_category_preference.repository import UserCategoryPreferenceRepository
from app.catalog.user_category_preference.schemas import (
    DomainPreferenceBulkUpdate,
    DomainPreferenceResponse,
    DomainPreferenceToggle,
)
from app.catalog.user_category_preference.service import (
    TechnologyDomainDisabledError,
    TechnologyDomainNotFoundError,
    UserCategoryPreferenceService,
)
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/me/domain-preferences", tags=["User Domain Preferences"])


def get_user_category_preference_service(
    db: Session = Depends(get_db),
) -> UserCategoryPreferenceService:
    return UserCategoryPreferenceService(
        UserCategoryPreferenceRepository(db),
        TechnologyDomainRepository(db),
        FeedRepository(db),
    )


@router.get("", response_model=list[DomainPreferenceResponse])
def list_domain_preferences(
    current_user: User = Depends(get_current_user),
    service: UserCategoryPreferenceService = Depends(get_user_category_preference_service),
) -> list[DomainPreferenceResponse]:
    return service.list_for_user(current_user.id)


@router.put("", response_model=list[DomainPreferenceResponse])
def bulk_update_domain_preferences(
    payload: DomainPreferenceBulkUpdate,
    current_user: User = Depends(get_current_user),
    service: UserCategoryPreferenceService = Depends(get_user_category_preference_service),
) -> list[DomainPreferenceResponse]:
    try:
        return service.bulk_update(current_user.id, payload)
    except TechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TechnologyDomainDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{technology_domain_id}", response_model=DomainPreferenceResponse)
def toggle_domain_preference(
    technology_domain_id: UUID,
    payload: DomainPreferenceToggle,
    current_user: User = Depends(get_current_user),
    service: UserCategoryPreferenceService = Depends(get_user_category_preference_service),
) -> DomainPreferenceResponse:
    try:
        return service.toggle(current_user.id, technology_domain_id, payload)
    except TechnologyDomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TechnologyDomainDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
