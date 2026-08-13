from __future__ import annotations

from app.api.auth.dependencies import get_current_employee
from app.infrastructure.employee_database.repository import EmployeeRecord
from fastapi import Depends, HTTPException, status

FEED_SOURCE_MANAGER_DESIGNATIONS = frozenset(
    {
        "super admin",
        "delivery manager",
    }
)


def can_manage_feed_sources(employee: EmployeeRecord) -> bool:
    designation = employee.designation.strip().casefold()
    return designation in FEED_SOURCE_MANAGER_DESIGNATIONS


def require_feed_source_manager(
    employee: EmployeeRecord = Depends(get_current_employee),
) -> EmployeeRecord:
    if not can_manage_feed_sources(employee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage feed sources.",
        )
    return employee
