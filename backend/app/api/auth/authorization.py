from __future__ import annotations

from app.api.auth.dependencies import get_current_employee
from app.api.auth.models import AuthenticatedUser
from fastapi import Depends, HTTPException, status


def can_manage_feed_sources(user: AuthenticatedUser) -> bool:
    return user.is_admin


def require_feed_source_manager(
    user: AuthenticatedUser = Depends(get_current_employee),
) -> AuthenticatedUser:
    if not can_manage_feed_sources(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage feed sources.",
        )
    return user
