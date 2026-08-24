from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    name: str
    designation: str = "Employee"
    emp_no: str | None = None
    is_admin: bool = False
