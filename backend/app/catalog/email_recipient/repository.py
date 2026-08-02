from uuid import UUID

from app.catalog.email_recipient.model import EmailRecipient
from app.catalog.email_recipient.schemas import EmailRecipientCreate
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class EmailRecipientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: EmailRecipientCreate) -> EmailRecipient:
        recipient = EmailRecipient(**payload.model_dump())
        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)
        return recipient

    def get_by_id(self, recipient_id: UUID) -> EmailRecipient | None:
        statement = select(EmailRecipient).where(EmailRecipient.id == recipient_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_email(self, email: str) -> EmailRecipient | None:
        statement = select(EmailRecipient).where(func.lower(EmailRecipient.email) == email.lower())
        return self.db.execute(statement).scalar_one_or_none()

    def list(self) -> list[EmailRecipient]:
        statement = select(EmailRecipient).order_by(EmailRecipient.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

    def delete(self, recipient: EmailRecipient) -> None:
        self.db.delete(recipient)
        self.db.commit()
