from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from app.catalog.technology_domain.model import TechnologyDomainSchedule
from app.catalog.user_category_preference.schemas import (
    DomainPreferenceBulkUpdate,
    DomainPreferenceItem,
    DomainPreferenceToggle,
)
from app.catalog.user_category_preference.service import (
    TechnologyDomainDisabledError,
    TechnologyDomainNotFoundError,
    UserCategoryPreferenceService,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
DOMAIN_ID = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _domain(**overrides: object) -> SimpleNamespace:
    domain = SimpleNamespace(
        id=DOMAIN_ID,
        name="AI",
        slug="ai",
        description="Artificial intelligence",
        is_enabled=True,
        frequency=TechnologyDomainSchedule.DAILY,
    )
    for key, value in overrides.items():
        setattr(domain, key, value)
    return domain


def _preference(**overrides: object) -> SimpleNamespace:
    preference = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        technology_domain_id=DOMAIN_ID,
        enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )
    for key, value in overrides.items():
        setattr(preference, key, value)
    return preference


def _service(
    *,
    domains: list[SimpleNamespace] | None = None,
    preferences: list[SimpleNamespace] | None = None,
    feed_counts: dict[UUID, int] | None = None,
) -> UserCategoryPreferenceService:
    preference_repository = MagicMock()
    technology_domain_repository = MagicMock()
    feed_repository = MagicMock()

    technology_domain_repository.list.return_value = domains or [_domain()]
    preference_repository.list_by_user_id.return_value = preferences or []
    feed_repository.count_by_technology_domain_ids.return_value = feed_counts or {DOMAIN_ID: 3}
    feed_repository.count_by_technology_domain_id.return_value = feed_counts.get(DOMAIN_ID, 3) if feed_counts else 3

    return UserCategoryPreferenceService(
        preference_repository,
        technology_domain_repository,
        feed_repository,
    )


def test_list_for_user_defaults_to_opt_in_disabled() -> None:
    result = _service().list_for_user(USER_ID)

    assert len(result) == 1
    assert result[0].user_enabled is False
    assert result[0].effective_enabled is False
    assert result[0].feed_count == 3


def test_list_for_user_merges_existing_preference() -> None:
    service = _service(preferences=[_preference(enabled=True)])
    result = service.list_for_user(USER_ID)

    assert result[0].user_enabled is True
    assert result[0].effective_enabled is True


def test_list_for_user_excludes_system_disabled_domains() -> None:
    service = _service(domains=[_domain(is_enabled=False)])
    result = service.list_for_user(USER_ID)

    assert result == []


def test_bulk_update_creates_preferences() -> None:
    service = _service()
    service.technology_domain_repository.get_by_id.return_value = _domain()
    payload = DomainPreferenceBulkUpdate(
        preferences=[DomainPreferenceItem(technology_domain_id=DOMAIN_ID, enabled=True)]
    )

    service.bulk_update(USER_ID, payload)

    service.preference_repository.upsert.assert_called_once_with(
        user_id=USER_ID,
        technology_domain_id=DOMAIN_ID,
        enabled=True,
    )


def test_bulk_update_rejects_enabling_system_disabled_domain() -> None:
    service = _service(domains=[_domain(is_enabled=False)])
    service.technology_domain_repository.get_by_id.return_value = _domain(is_enabled=False)
    payload = DomainPreferenceBulkUpdate(
        preferences=[DomainPreferenceItem(technology_domain_id=DOMAIN_ID, enabled=True)]
    )

    with pytest.raises(TechnologyDomainDisabledError):
        service.bulk_update(USER_ID, payload)


def test_toggle_returns_updated_preference() -> None:
    service = _service(preferences=[_preference(enabled=True)])
    service.preference_repository.get_by_user_and_domain.return_value = _preference(enabled=True)
    service.technology_domain_repository.get_by_id.return_value = _domain()

    result = service.toggle(
        USER_ID,
        DOMAIN_ID,
        DomainPreferenceToggle(enabled=True),
    )

    assert result.user_enabled is True
    assert result.effective_enabled is True


def test_toggle_unknown_domain_raises_not_found() -> None:
    service = _service()
    service.technology_domain_repository.get_by_id.return_value = None

    with pytest.raises(TechnologyDomainNotFoundError):
        service.toggle(USER_ID, DOMAIN_ID, DomainPreferenceToggle(enabled=True))
