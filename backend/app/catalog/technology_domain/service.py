from uuid import UUID

from app.catalog.technology_domain.model import TechnologyDomain
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.catalog.technology_domain.schemas import TechnologyDomainCreate, TechnologyDomainUpdate
from sqlalchemy.exc import IntegrityError


class TechnologyDomainNotFoundError(Exception):
    pass


class TechnologyDomainDuplicateNameError(Exception):
    pass


class TechnologyDomainService:
    def __init__(self, repository: TechnologyDomainRepository):
        self.repository = repository

    def create(self, payload: TechnologyDomainCreate) -> TechnologyDomain:
        if self.repository.get_by_name(payload.name):
            raise TechnologyDomainDuplicateNameError(
                f"Technology domain with name '{payload.name}' already exists."
            )
        if self.repository.get_by_slug(payload.slug):
            raise TechnologyDomainDuplicateNameError(
                f"Technology domain with slug '{payload.slug}' already exists."
            )

        try:
            return self.repository.create(payload)
        except IntegrityError as exc:
            raise TechnologyDomainDuplicateNameError(
                f"Technology domain with name '{payload.name}' already exists."
            ) from exc

    def get_by_id(self, domain_id: UUID) -> TechnologyDomain:
        domain = self.repository.get_by_id(domain_id)
        if domain is None:
            raise TechnologyDomainNotFoundError(
                f"Technology domain with id '{domain_id}' was not found."
            )
        return domain

    def list(self) -> list[TechnologyDomain]:
        return self.repository.list()

    def update(
        self, domain_id: UUID, payload: TechnologyDomainUpdate
    ) -> TechnologyDomain:
        domain = self.get_by_id(domain_id)

        if payload.name is not None:
            existing = self.repository.get_by_name(payload.name)
            if existing is not None and existing.id != domain.id:
                raise TechnologyDomainDuplicateNameError(
                    f"Technology domain with name '{payload.name}' already exists."
                )

        if payload.slug is not None:
            existing = self.repository.get_by_slug(payload.slug)
            if existing is not None and existing.id != domain.id:
                raise TechnologyDomainDuplicateNameError(
                    f"Technology domain with slug '{payload.slug}' already exists."
                )

        try:
            return self.repository.update(domain, payload)
        except IntegrityError as exc:
            raise TechnologyDomainDuplicateNameError(
                "Technology domain name must be unique."
            ) from exc

    def delete(self, domain_id: UUID) -> None:
        domain = self.get_by_id(domain_id)
        self.repository.delete(domain)

