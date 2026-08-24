from uuid import UUID

from app.catalog.feed.repository import FeedRepository
from app.catalog.technology_domain.model import TechnologyDomain, TechnologyDomainSchedule
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.catalog.user_category_preference.repository import UserCategoryPreferenceRepository
from app.catalog.user_category_preference.schemas import (
    DomainPreferenceBulkUpdate,
    DomainPreferenceItem,
    DomainPreferenceResponse,
    DomainPreferenceToggle,
)


class TechnologyDomainDisabledError(Exception):
    pass


class TechnologyDomainNotFoundError(Exception):
    pass


class UserCategoryPreferenceService:
    def __init__(
        self,
        preference_repository: UserCategoryPreferenceRepository,
        technology_domain_repository: TechnologyDomainRepository,
        feed_repository: FeedRepository,
    ) -> None:
        self.preference_repository = preference_repository
        self.technology_domain_repository = technology_domain_repository
        self.feed_repository = feed_repository

    def list_for_user(self, user_id: UUID) -> list[DomainPreferenceResponse]:
        domains = self.technology_domain_repository.list()
        preferences = {
            preference.technology_domain_id: preference
            for preference in self.preference_repository.list_by_user_id(user_id)
        }
        feed_counts = self.feed_repository.count_by_technology_domain_ids(
            [domain.id for domain in domains]
        )
        return [
            self._to_response(
                domain,
                preferences.get(domain.id),
                feed_counts.get(domain.id, 0),
            )
            for domain in domains
            if domain.is_enabled
        ]

    def bulk_update(
        self,
        user_id: UUID,
        payload: DomainPreferenceBulkUpdate,
    ) -> list[DomainPreferenceResponse]:
        for item in payload.preferences:
            self._upsert_preference(user_id, item)
        return self.list_for_user(user_id)

    def list_effective_enabled_for_schedule(
        self,
        user_id: UUID,
        schedule: TechnologyDomainSchedule,
    ) -> set[UUID]:
        domains = self.technology_domain_repository.list()
        preferences = {
            preference.technology_domain_id: preference
            for preference in self.preference_repository.list_by_user_id(user_id)
        }
        enabled: set[UUID] = set()
        for domain in domains:
            if not domain.is_enabled or domain.schedule != schedule:
                continue
            preference = preferences.get(domain.id)
            user_enabled = preference.enabled if preference is not None else False
            if user_enabled:
                enabled.add(domain.id)
        return enabled

    def toggle(
        self,
        user_id: UUID,
        technology_domain_id: UUID,
        payload: DomainPreferenceToggle,
    ) -> DomainPreferenceResponse:
        domain = self._get_system_enabled_domain(technology_domain_id)
        if payload.enabled and not domain.is_enabled:
            raise TechnologyDomainDisabledError(
                "Cannot enable a technology domain that is disabled by the system."
            )
        self.preference_repository.upsert(
            user_id=user_id,
            technology_domain_id=technology_domain_id,
            enabled=payload.enabled,
        )
        feed_count = self.feed_repository.count_by_technology_domain_id(technology_domain_id)
        preference = self.preference_repository.get_by_user_and_domain(
            user_id,
            technology_domain_id,
        )
        return self._to_response(domain, preference, feed_count)

    def _upsert_preference(self, user_id: UUID, item: DomainPreferenceItem) -> None:
        domain = self.technology_domain_repository.get_by_id(item.technology_domain_id)
        if domain is None:
            raise TechnologyDomainNotFoundError(
                f"Technology domain with id '{item.technology_domain_id}' was not found."
            )
        if item.enabled and not domain.is_enabled:
            raise TechnologyDomainDisabledError(
                "Cannot enable a technology domain that is disabled by the system."
            )
        self.preference_repository.upsert(
            user_id=user_id,
            technology_domain_id=item.technology_domain_id,
            enabled=item.enabled,
        )

    def _get_system_enabled_domain(self, technology_domain_id: UUID) -> TechnologyDomain:
        domain = self.technology_domain_repository.get_by_id(technology_domain_id)
        if domain is None:
            raise TechnologyDomainNotFoundError(
                f"Technology domain with id '{technology_domain_id}' was not found."
            )
        return domain

    @staticmethod
    def _to_response(
        domain: TechnologyDomain,
        preference,
        feed_count: int,
    ) -> DomainPreferenceResponse:
        user_enabled = preference.enabled if preference is not None else False
        system_enabled = domain.is_enabled
        return DomainPreferenceResponse(
            technology_domain_id=domain.id,
            name=domain.name,
            slug=domain.slug,
            description=domain.description,
            frequency=domain.frequency,
            system_enabled=system_enabled,
            user_enabled=user_enabled,
            effective_enabled=system_enabled and user_enabled,
            feed_count=feed_count,
        )
