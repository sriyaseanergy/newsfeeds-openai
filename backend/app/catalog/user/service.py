from __future__ import annotations

from datetime import datetime, timezone

from app.catalog.user.model import User
from app.catalog.user.repository import UserRepository
from app.catalog.user.schemas import EntraIdentity
from sqlalchemy.exc import IntegrityError


class UserConflictError(Exception):
    """Raised when a user row cannot be resolved after an identity conflict."""


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def record_login(self, identity: EntraIdentity) -> User:
        now = datetime.now(timezone.utc)
        tenant_id = identity.tid.strip()
        entra_object_id = identity.oid.strip()

        existing = self.repository.get_by_tenant_and_entra_object_id(
            tenant_id,
            entra_object_id,
        )
        if existing is not None:
            self._apply_identity_updates(existing, identity, last_login_at=now)
            return self.repository.save(existing)

        try:
            return self.repository.create(
                tenant_id=tenant_id,
                entra_object_id=entra_object_id,
                email=self._optional_email(identity.email),
                display_name=self._optional_display_name(identity.display_name),
                last_login_at=now,
            )
        except IntegrityError as exc:
            self.repository.rollback()
            raced = self.repository.get_by_tenant_and_entra_object_id(
                tenant_id,
                entra_object_id,
            )
            if raced is None:
                raise UserConflictError(
                    "User identity conflict could not be resolved after duplicate insert."
                ) from exc
            self._apply_identity_updates(raced, identity, last_login_at=now)
            return self.repository.save(raced)

    @staticmethod
    def _optional_email(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        return normalized or None

    @staticmethod
    def _optional_display_name(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _apply_identity_updates(
        self,
        user: User,
        identity: EntraIdentity,
        *,
        last_login_at: datetime,
    ) -> None:
        user.last_login_at = last_login_at
        email = self._optional_email(identity.email)
        if email is not None:
            user.email = email
        display_name = self._optional_display_name(identity.display_name)
        if display_name is not None:
            user.display_name = display_name
