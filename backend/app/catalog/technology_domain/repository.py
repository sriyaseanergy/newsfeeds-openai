from uuid import UUID

from app.catalog.technology_domain.model import TechnologyDomain
from app.catalog.technology_domain.schemas import TechnologyDomainCreate, TechnologyDomainUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session


class TechnologyDomainRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: TechnologyDomainCreate) -> TechnologyDomain:
        data = payload.model_dump()
        is_enabled = data.pop("is_enabled")
        domain = TechnologyDomain(**data, is_active=is_enabled)
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        return domain

    def get_by_id(self, domain_id: UUID) -> TechnologyDomain | None:
        statement = select(TechnologyDomain).where(TechnologyDomain.id == domain_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_name(self, name: str) -> TechnologyDomain | None:
        statement = select(TechnologyDomain).where(TechnologyDomain.name == name)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> TechnologyDomain | None:
        statement = select(TechnologyDomain).where(TechnologyDomain.slug == slug)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self) -> list[TechnologyDomain]:
        statement = select(TechnologyDomain).order_by(TechnologyDomain.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

    def update(
        self, domain: TechnologyDomain, payload: TechnologyDomainUpdate
    ) -> TechnologyDomain:
        update_data = payload.model_dump(exclude_unset=True)
        if "is_enabled" in update_data:
            update_data["is_active"] = update_data.pop("is_enabled")
        for field, value in update_data.items():
            setattr(domain, field, value)

        self.db.commit()
        self.db.refresh(domain)
        return domain

    def delete(self, domain: TechnologyDomain) -> None:
        self.db.delete(domain)
        self.db.commit()

