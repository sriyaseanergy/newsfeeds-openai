from uuid import UUID

from app.catalog.email_recipient.model import EmailRecipient
from app.catalog.email_recipient.repository import EmailRecipientRepository
from app.catalog.email_recipient.schemas import EmailRecipientCreate
from sqlalchemy.exc import IntegrityError


class EmailRecipientNotFoundError(Exception):
    pass


class EmailRecipientDuplicateEmailError(Exception):
    pass


class EmailRecipientService:
    def __init__(self, repository: EmailRecipientRepository):
        self.repository = repository

    def create(self, payload: EmailRecipientCreate) -> EmailRecipient:
        existing = self.repository.get_by_email(payload.email)
        if existing is not None:
            raise EmailRecipientDuplicateEmailError(
                f"Email recipient with email '{payload.email}' already exists."
            )

        try:
            return self.repository.create(payload)
        except IntegrityError as exc:
            raise EmailRecipientDuplicateEmailError(
                f"Email recipient with email '{payload.email}' already exists."
            ) from exc

    def list(self) -> list[EmailRecipient]:
        return self.repository.list()

    def delete(self, recipient_id: UUID) -> None:
        recipient = self.repository.get_by_id(recipient_id)
        if recipient is None:
            raise EmailRecipientNotFoundError(
                f"Email recipient with id '{recipient_id}' was not found."
            )
        self.repository.delete(recipient)
