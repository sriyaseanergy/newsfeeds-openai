from datetime import datetime

from app.catalog.user.model import User
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_tenant_and_entra_object_id(
        self,
        tenant_id: str,
        entra_object_id: str,
    ) -> User | None:
        statement = select(User).where(
            User.tenant_id == tenant_id,
            User.entra_object_id == entra_object_id,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def create(
        self,
        *,
        tenant_id: str,
        entra_object_id: str,
        email: str | None,
        display_name: str | None,
        last_login_at: datetime,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            entra_object_id=entra_object_id,
            email=email,
            display_name=display_name,
            last_login_at=last_login_at,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def rollback(self) -> None:
        self.db.rollback()
