from __future__ import annotations

from app.api.auth.authorization import (
    can_manage_feed_sources,
    require_feed_source_manager,
)
from app.api.auth.dependencies import get_current_employee
from app.api.auth.models import AuthenticatedUser
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _user(email: str, *, is_admin: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        email=email,
        name="Test User",
        designation="Employee",
        emp_no=None,
        is_admin=is_admin,
    )


@pytest.mark.parametrize("is_admin", [True])
def test_can_manage_feed_sources_allows_admin(is_admin: bool) -> None:
    assert can_manage_feed_sources(_user("admin@example.com", is_admin=is_admin)) is True


def test_can_manage_feed_sources_denies_non_admin() -> None:
    assert can_manage_feed_sources(_user("other@example.com", is_admin=False)) is False


def _build_test_client(user: AuthenticatedUser) -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected_route(
        authenticated_user: AuthenticatedUser = Depends(require_feed_source_manager),
    ) -> dict[str, str | None]:
        return {"email": authenticated_user.email, "emp_no": authenticated_user.emp_no}

    app.dependency_overrides[get_current_employee] = lambda: user
    return TestClient(app)


def test_require_feed_source_manager_allows_admin() -> None:
    client = _build_test_client(_user("admin@example.com", is_admin=True))
    response = client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com", "emp_no": None}


def test_require_feed_source_manager_returns_403_for_non_admin() -> None:
    client = _build_test_client(_user("other@example.com", is_admin=False))
    response = client.get("/protected")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }
