from __future__ import annotations

import app.infrastructure.database.model_registry  # noqa: F401
import pytest
from app.catalog.technology_domain.model import (
    InvalidTechnologyDomainFrequencyError,
    TechnologyDomain,
    TechnologyDomainFrequency,
    TechnologyDomainSchedule,
    parse_technology_domain_frequency,
)
from app.catalog.technology_domain.schemas import TechnologyDomainCreate
from pydantic import ValidationError


def test_technology_domain_create_schema_requires_slug_and_validates_format() -> None:
    payload = TechnologyDomainCreate(
        name="AI Security",
        slug="ai-security",
        description="Daily security intelligence",
    )

    assert payload.name == "AI Security"
    assert payload.slug == "ai-security"
    assert payload.is_enabled is True


def test_technology_domain_create_schema_rejects_invalid_slug() -> None:
    with pytest.raises(ValidationError):
        TechnologyDomainCreate(name="AI Security", slug="AI Security")


def test_model_accepts_daily_frequency() -> None:
    domain = TechnologyDomain(
        name="AI Security",
        slug="ai-security",
        frequency=TechnologyDomainSchedule.DAILY,
    )

    assert domain.frequency is TechnologyDomainSchedule.DAILY
    assert domain.configured_frequency is TechnologyDomainFrequency.DAILY
    assert domain.schedule is TechnologyDomainSchedule.DAILY


def test_model_accepts_weekly_frequency() -> None:
    domain = TechnologyDomain(
        name="Engineering",
        slug="engineering",
        frequency=TechnologyDomainSchedule.WEEKLY,
    )

    assert domain.configured_frequency is TechnologyDomainFrequency.WEEKLY


@pytest.mark.parametrize("invalid_value", ["MONTHLY", "MANUAL", "", "daily-weekly"])
def test_parse_technology_domain_frequency_rejects_invalid_values(
    invalid_value: str,
) -> None:
    with pytest.raises(InvalidTechnologyDomainFrequencyError):
        parse_technology_domain_frequency(invalid_value)


def test_parse_technology_domain_frequency_accepts_daily_and_weekly() -> None:
    assert (
        parse_technology_domain_frequency("daily")
        is TechnologyDomainFrequency.DAILY
    )
    assert (
        parse_technology_domain_frequency(TechnologyDomainSchedule.WEEKLY)
        is TechnologyDomainFrequency.WEEKLY
    )


def test_model_is_enabled_alias_maps_to_is_active() -> None:
    domain = TechnologyDomain(name="Platform", slug="platform")

    domain.is_enabled = False

    assert domain.is_active is False
    assert domain.is_enabled is False
