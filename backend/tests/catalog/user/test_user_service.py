from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from unittest.mock import MagicMock, patch

import pytest
from app.api.auth.admin_emails import is_feed_source_admin
from app.catalog.user.schemas import EntraIdentity
from app.catalog.user.service import UserConflictError, UserService
from app.core.settings import Settings
from sqlalchemy.exc import IntegrityError

TENANT_ID = "647119b9-2120-453d-ab27-e02884c15a1b"
OBJECT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
USER_ID = UUID("11111111-2222-3333-4444-555555555555")


def _identity(**overrides: object) -> EntraIdentity:
    base = {
        "oid": OBJECT_ID,
        "tid": TENANT_ID,
        "email": "user@example.com",
        "display_name": "Jane Doe",
    }
    base.update(overrides)
    return EntraIdentity(**base)


def _existing_user(**overrides: object) -> SimpleNamespace:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user = SimpleNamespace(
        id=USER_ID,
        tenant_id=TENANT_ID,
        entra_object_id=OBJECT_ID,
        email="old@example.com",
        display_name="Old Name",
        last_login_at=now,
        is_active=True,
        is_admin=False,
        created_at=now,
        updated_at=now,
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


def test_record_login_creates_user_when_not_found() -> None:
    repository = MagicMock()
    repository.get_by_tenant_and_entra_object_id.return_value = None
    created = _existing_user(id=uuid4(), email="user@example.com", display_name="Jane Doe")
    repository.create.return_value = created

    result = UserService(repository).record_login(_identity())

    assert result is created
    repository.create.assert_called_once()
    kwargs = repository.create.call_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["entra_object_id"] == OBJECT_ID
    assert kwargs["email"] == "user@example.com"
    assert kwargs["display_name"] == "Jane Doe"
    assert kwargs["last_login_at"].tzinfo is not None
    repository.save.assert_not_called()


def test_record_login_updates_existing_user_and_preserves_uuid() -> None:
    repository = MagicMock()
    existing = _existing_user()
    repository.get_by_tenant_and_entra_object_id.return_value = existing
    repository.save.side_effect = lambda user: user

    result = UserService(repository).record_login(
        _identity(email="new@example.com", display_name="New Name")
    )

    assert result.id == USER_ID
    assert result.email == "new@example.com"
    assert result.display_name == "New Name"
    assert result.last_login_at > datetime(2026, 1, 2, tzinfo=timezone.utc)
    repository.create.assert_not_called()
    repository.save.assert_called_once_with(existing)


def test_record_login_preserves_email_and_display_name_when_not_provided() -> None:
    repository = MagicMock()
    existing = _existing_user()
    repository.get_by_tenant_and_entra_object_id.return_value = existing
    repository.save.side_effect = lambda user: user

    result = UserService(repository).record_login(
        _identity(email=None, display_name=None)
    )

    assert result.email == "old@example.com"
    assert result.display_name == "Old Name"
    repository.create.assert_not_called()


def test_record_login_is_idempotent_for_existing_identity() -> None:
    repository = MagicMock()
    existing = _existing_user()
    repository.get_by_tenant_and_entra_object_id.return_value = existing
    repository.save.side_effect = lambda user: user
    service = UserService(repository)

    first = service.record_login(_identity())
    second = service.record_login(_identity())

    assert first.id == second.id == USER_ID
    assert repository.create.call_count == 0
    assert repository.save.call_count == 2


def test_record_login_retries_after_integrity_conflict() -> None:
    repository = MagicMock()
    raced = _existing_user(email="user@example.com", display_name="Jane Doe")
    repository.get_by_tenant_and_entra_object_id.side_effect = [None, raced]
    repository.create.side_effect = IntegrityError("duplicate", {}, Exception())
    repository.save.side_effect = lambda user: user

    result = UserService(repository).record_login(_identity())

    assert result.id == USER_ID
    repository.rollback.assert_called_once()
    repository.save.assert_called_once_with(raced)


def test_record_login_raises_when_integrity_conflict_unresolved() -> None:
    repository = MagicMock()
    repository.get_by_tenant_and_entra_object_id.return_value = None
    repository.create.side_effect = IntegrityError("duplicate", {}, Exception())

    with pytest.raises(UserConflictError):
        UserService(repository).record_login(_identity())

    repository.rollback.assert_called_once()


def test_record_login_bootstraps_admin_from_env_on_create() -> None:
    repository = MagicMock()
    repository.get_by_tenant_and_entra_object_id.return_value = None
    created = _existing_user(is_admin=True)
    repository.create.return_value = created
    settings = Settings(
        azure_tenant_id=TENANT_ID,
        azure_auth_client_id="6442ff78-2021-4ee3-8dd3-b0b04cae8066",
        feed_source_admin_emails="user@example.com",
    )

    UserService(repository, settings=settings).record_login(_identity())

    assert repository.create.call_args.kwargs["is_admin"] is True


def test_record_login_promotes_existing_user_to_admin_without_demotion() -> None:
    repository = MagicMock()
    existing = _existing_user(is_admin=False)
    repository.get_by_tenant_and_entra_object_id.return_value = existing
    repository.save.side_effect = lambda user: user
    settings = Settings(
        azure_tenant_id=TENANT_ID,
        azure_auth_client_id="6442ff78-2021-4ee3-8dd3-b0b04cae8066",
        feed_source_admin_emails="user@example.com",
    )

    result = UserService(repository, settings=settings).record_login(_identity())

    assert result.is_admin is True
    repository.save.assert_called_once_with(existing)


def test_record_login_never_demotes_admin_when_removed_from_env() -> None:
    repository = MagicMock()
    existing = _existing_user(is_admin=True)
    repository.get_by_tenant_and_entra_object_id.return_value = existing
    repository.save.side_effect = lambda user: user
    settings = Settings(
        azure_tenant_id=TENANT_ID,
        azure_auth_client_id="6442ff78-2021-4ee3-8dd3-b0b04cae8066",
        feed_source_admin_emails="",
    )

    result = UserService(repository, settings=settings).record_login(_identity())

    assert result.is_admin is True
