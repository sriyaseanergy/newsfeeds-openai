from uuid import UUID

from app.catalog.email_recipient.repository import EmailRecipientRepository
from app.catalog.email_recipient.schemas import EmailRecipientCreate, EmailRecipientResponse
from app.catalog.email_recipient.service import (
    EmailRecipientDuplicateEmailError,
    EmailRecipientNotFoundError,
    EmailRecipientService,
)
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/email-recipients", tags=["Email Recipients"])


def get_email_recipient_service(
    db: Session = Depends(get_db),
) -> EmailRecipientService:
    repository = EmailRecipientRepository(db)
    return EmailRecipientService(repository)


@router.get("", response_model=list[EmailRecipientResponse])
def list_email_recipients(
    service: EmailRecipientService = Depends(get_email_recipient_service),
) -> list[EmailRecipientResponse]:
    return service.list()


@router.post(
    "",
    response_model=EmailRecipientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_email_recipient(
    payload: EmailRecipientCreate,
    service: EmailRecipientService = Depends(get_email_recipient_service),
) -> EmailRecipientResponse:
    try:
        return service.create(payload)
    except EmailRecipientDuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_recipient(
    recipient_id: UUID,
    service: EmailRecipientService = Depends(get_email_recipient_service),
) -> Response:
    try:
        service.delete(recipient_id)
    except EmailRecipientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
