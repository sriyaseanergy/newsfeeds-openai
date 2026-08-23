from uuid import UUID

from app.catalog.user_category_preference.model import UserCategoryPreference
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserCategoryPreferenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user_id(self, user_id: UUID) -> list[UserCategoryPreference]:
        statement = (
            select(UserCategoryPreference)
            .where(UserCategoryPreference.user_id == user_id)
            .order_by(UserCategoryPreference.created_at.asc())
        )
        return list(self.db.execute(statement).scalars().all())

    def get_by_user_and_domain(
        self,
        user_id: UUID,
        technology_domain_id: UUID,
    ) -> UserCategoryPreference | None:
        statement = select(UserCategoryPreference).where(
            UserCategoryPreference.user_id == user_id,
            UserCategoryPreference.technology_domain_id == technology_domain_id,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def upsert(
        self,
        *,
        user_id: UUID,
        technology_domain_id: UUID,
        enabled: bool,
    ) -> UserCategoryPreference:
        existing = self.get_by_user_and_domain(user_id, technology_domain_id)
        if existing is not None:
            existing.enabled = enabled
            self.db.commit()
            self.db.refresh(existing)
            return existing

        preference = UserCategoryPreference(
            user_id=user_id,
            technology_domain_id=technology_domain_id,
            enabled=enabled,
        )
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference
