from __future__ import annotations

from datetime import datetime, timezone

from app.api.auth.admin_emails import is_feed_source_admin
from app.catalog.user.model import User
from app.catalog.user.repository import UserRepository
from app.catalog.user.schemas import EntraIdentity
from app.core.settings import Settings, get_settings
from sqlalchemy.exc import IntegrityError


class UserConflictError(Exception):
    """Raised when a user row cannot be resolved after an identity conflict."""


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self._settings = settings or get_settings()

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
            self._maybe_promote_admin(existing, identity.email)
            return self.repository.save(existing)

        email = self._optional_email(identity.email)
        try:
            return self.repository.create(
                tenant_id=tenant_id,
                entra_object_id=entra_object_id,
                email=email,
                display_name=self._optional_display_name(identity.display_name),
                last_login_at=now,
                is_admin=self._should_bootstrap_admin(email),
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
            self._maybe_promote_admin(raced, identity.email)
            return self.repository.save(raced)

    def _should_bootstrap_admin(self, email: str | None) -> bool:
        if email is None:
            return False
        return is_feed_source_admin(email, self._settings)

    def _maybe_promote_admin(self, user: User, email: str | None) -> None:
        if user.is_admin:
            return
        normalized = self._optional_email(email)
        if normalized is not None and is_feed_source_admin(normalized, self._settings):
            user.is_admin = True

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
