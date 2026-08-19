from __future__ import annotations

from uuid import uuid4

import app.infrastructure.database.model_registry  # noqa: F401
from app.catalog.user_category_preference.model import UserCategoryPreference
from sqlalchemy import UniqueConstraint


def test_valid_preference_creation() -> None:
    user_id = uuid4()
    technology_domain_id = uuid4()

    preference = UserCategoryPreference(
        user_id=user_id,
        technology_domain_id=technology_domain_id,
    )

    assert preference.user_id == user_id
    assert preference.technology_domain_id == technology_domain_id
    assert UserCategoryPreference.__table__.c.id.primary_key is True


def test_enabled_defaults_to_true() -> None:
    enabled_column = UserCategoryPreference.__table__.c.enabled

    assert enabled_column.default.arg is True
    assert str(enabled_column.server_default.arg) == "true"


def test_user_foreign_key() -> None:
    foreign_keys = {
        foreign_key.parent.name: foreign_key.target_fullname
        for foreign_key in UserCategoryPreference.__table__.foreign_keys
    }

    assert foreign_keys["user_id"] == "users.id"


def test_technology_domain_foreign_key() -> None:
    foreign_keys = {
        foreign_key.parent.name: foreign_key.target_fullname
        for foreign_key in UserCategoryPreference.__table__.foreign_keys
    }

    assert foreign_keys["technology_domain_id"] == "technology_domains.id"


def test_duplicate_user_domain_pair_is_prevented() -> None:
    unique_constraints = [
        constraint
        for constraint in UserCategoryPreference.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    matching = [
        constraint
        for constraint in unique_constraints
        if {column.name for column in constraint.columns}
        == {"user_id", "technology_domain_id"}
    ]

    assert len(matching) == 1
    assert (
        matching[0].name
        == "uq_user_category_preferences_user_id_technology_domain_id"
    )
