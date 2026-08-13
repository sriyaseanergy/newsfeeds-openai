from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from app.api.auth.dependencies import get_current_employee
from app.catalog.feed.model import FetchKind
from app.catalog.feed.router import get_feed_service, router as feed_router
from app.catalog.feed.schemas import FeedCreate, FeedResponse, FeedUpdate
from app.infrastructure.employee_database.repository import EmployeeRecord
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

FEED_ID = UUID("11111111-1111-1111-1111-111111111111")
DOMAIN_ID = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _employee(designation: str) -> EmployeeRecord:
    return EmployeeRecord(
        emp_no="E001",
        name="Test User",
        email="test.user@example.com",
        designation=designation,
    )


def _sample_feed_response() -> FeedResponse:
    return FeedResponse(
        id=FEED_ID,
        technology_domain_id=DOMAIN_ID,
        name="Example Feed",
        description=None,
        url="https://example.com/rss",
        is_enabled=True,
        fetch_kind=FetchKind.RSS,
        crawl_depth=1,
        max_new_articles_per_crawl=20,
        created_at=NOW,
        updated_at=NOW,
    )


def _create_payload() -> dict[str, object]:
    return {
        "technology_domain_id": str(DOMAIN_ID),
        "name": "Example Feed",
        "url": "https://example.com/rss",
    }


def _update_payload() -> dict[str, object]:
    return {"name": "Updated Feed"}


@pytest.fixture
def mock_feed_service() -> MagicMock:
    service = MagicMock()
    service.create.return_value = _sample_feed_response()
    service.update.return_value = _sample_feed_response()
    service.delete.return_value = None
    service.list.return_value = [_sample_feed_response()]
    return service


@pytest.fixture
def client(mock_feed_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(feed_router)
    app.dependency_overrides[get_feed_service] = lambda: mock_feed_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _set_employee(client: TestClient, employee: EmployeeRecord | None) -> None:
    app = client.app
    if employee is None:
        app.dependency_overrides.pop(get_current_employee, None)
        return
    app.dependency_overrides[get_current_employee] = lambda: employee


@pytest.mark.parametrize("designation", ["Super Admin", "Delivery Manager"])
def test_authorized_employee_can_create_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    designation: str,
) -> None:
    _set_employee(client, _employee(designation))
    response = client.post("/feeds", json=_create_payload())
    assert response.status_code == 201
    assert response.json()["name"] == "Example Feed"
    mock_feed_service.create.assert_called_once()
    create_payload = mock_feed_service.create.call_args.args[0]
    assert isinstance(create_payload, FeedCreate)
    assert create_payload.name == "Example Feed"


@pytest.mark.parametrize("designation", ["Super Admin", "Delivery Manager"])
def test_authorized_employee_can_update_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    designation: str,
) -> None:
    _set_employee(client, _employee(designation))
    response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
    assert response.status_code == 200
    assert response.json()["name"] == "Example Feed"
    mock_feed_service.update.assert_called_once_with(FEED_ID, FeedUpdate(name="Updated Feed"))


@pytest.mark.parametrize("designation", ["Super Admin", "Delivery Manager"])
def test_authorized_employee_can_delete_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    designation: str,
) -> None:
    _set_employee(client, _employee(designation))
    response = client.delete(f"/feeds/{FEED_ID}")
    assert response.status_code == 204
    mock_feed_service.delete.assert_called_once_with(FEED_ID)


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_unauthorized_designation_receives_403(
    client: TestClient,
    mock_feed_service: MagicMock,
    method: str,
) -> None:
    _set_employee(client, _employee("Software Engineer"))
    if method == "post":
        response = client.post("/feeds", json=_create_payload())
    elif method == "put":
        response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
    else:
        response = client.delete(f"/feeds/{FEED_ID}")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }
    mock_feed_service.create.assert_not_called()
    mock_feed_service.update.assert_not_called()
    mock_feed_service.delete.assert_not_called()


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_unauthenticated_request_receives_401(
    client: TestClient,
    mock_feed_service: MagicMock,
    method: str,
) -> None:
    _set_employee(client, None)
    if method == "post":
        response = client.post("/feeds", json=_create_payload())
    elif method == "put":
        response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
    else:
        response = client.delete(f"/feeds/{FEED_ID}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid authentication."}
    mock_feed_service.create.assert_not_called()
    mock_feed_service.update.assert_not_called()
    mock_feed_service.delete.assert_not_called()


def test_list_feeds_remains_unauthenticated(
    client: TestClient,
    mock_feed_service: MagicMock,
) -> None:
    _set_employee(client, None)
    response = client.get("/feeds")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Example Feed"
    mock_feed_service.list.assert_called_once()
