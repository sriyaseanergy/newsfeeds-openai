from __future__ import annotations

from app.api.auth.admin_emails import is_feed_source_admin
from app.api.auth.dependencies import get_current_employee
from app.api.auth.models import AuthenticatedUser
from app.core.settings import Settings, get_settings
from fastapi import Depends, HTTPException, status


def can_manage_feed_sources(
    user: AuthenticatedUser,
    settings: Settings | None = None,
) -> bool:
    resolved_settings = settings or get_settings()
    return is_feed_source_admin(user.email, resolved_settings)


def require_feed_source_manager(
    user: AuthenticatedUser = Depends(get_current_employee),
) -> AuthenticatedUser:
    if not can_manage_feed_sources(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage feed sources.",
        )
    return user
