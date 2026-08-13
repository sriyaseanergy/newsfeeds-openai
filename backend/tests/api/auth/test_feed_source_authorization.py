from app.api.auth.authorization import (
    can_manage_feed_sources,
    require_feed_source_manager,
)
from app.api.auth.dependencies import get_current_employee
from app.infrastructure.employee_database.repository import EmployeeRecord
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _employee(designation: str) -> EmployeeRecord:
    return EmployeeRecord(
        emp_no="E001",
        name="Test User",
        email="test.user@example.com",
        designation=designation,
    )


@pytest.mark.parametrize(
    "designation",
    ["Super Admin", "super admin", "SUPER ADMIN", "Delivery Manager", "delivery manager"],
)
def test_can_manage_feed_sources_allows_legacy_designations(designation: str) -> None:
    assert can_manage_feed_sources(_employee(designation)) is True


@pytest.mark.parametrize(
    "designation",
    ["Software Engineer", "Analyst", "", "Admin"],
)
def test_can_manage_feed_sources_denies_other_designations(designation: str) -> None:
    assert can_manage_feed_sources(_employee(designation)) is False


def _build_test_client(employee: EmployeeRecord) -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected_route(
        authenticated_employee: EmployeeRecord = Depends(require_feed_source_manager),
    ) -> dict[str, str]:
        return {"emp_no": authenticated_employee.emp_no}

    app.dependency_overrides[get_current_employee] = lambda: employee
    return TestClient(app)


@pytest.mark.parametrize("designation", ["Super Admin", "Delivery Manager"])
def test_require_feed_source_manager_allows_authorized_designations(
    designation: str,
) -> None:
    client = _build_test_client(_employee(designation))
    response = client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"emp_no": "E001"}


def test_require_feed_source_manager_returns_403_for_other_designation() -> None:
    client = _build_test_client(_employee("Software Engineer"))
    response = client.get("/protected")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }
