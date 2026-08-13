from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.settings import Settings
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class EmployeeRecord:
    emp_no: str
    name: str
    email: str
    designation: str


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str, label: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        msg = f"Invalid MyWork {label}: {value!r}"
        raise ValueError(msg)
    return value


class EmployeeRepository:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._table = _validate_identifier(settings.mywork_employee_table, "table name")
        self._emp_no_column = _validate_identifier(
            settings.mywork_emp_no_column,
            "emp_no column",
        )
        self._name_column = _validate_identifier(
            settings.mywork_name_column,
            "name column",
        )
        self._email_column = _validate_identifier(
            settings.mywork_email_column,
            "email column",
        )
        self._designation_column = _validate_identifier(
            settings.mywork_designation_column,
            "designation column",
        )
        self._last_day_column = _validate_identifier(
            settings.mywork_last_day_column,
            "LastDay column",
        )

    def find_active_by_email(self, email: str) -> EmployeeRecord | None:
        query = text(
            f"""
            SELECT
                [{self._emp_no_column}] AS emp_no,
                [{self._name_column}] AS name,
                [{self._email_column}] AS email,
                [{self._designation_column}] AS designation
            FROM [{self._table}]
            WHERE LOWER([{self._email_column}]) = LOWER(:email)
              AND [{self._last_day_column}] IS NULL
            """
        )
        row = self._db.execute(query, {"email": email.strip()}).mappings().first()
        if row is None:
            return None

        emp_no = str(row["emp_no"]).strip()
        name = str(row["name"]).strip()
        row_email = str(row["email"]).strip()
        designation = str(row["designation"]).strip()
        if not emp_no or not name or not row_email or not designation:
            return None

        return EmployeeRecord(
            emp_no=emp_no,
            name=name,
            email=row_email.lower(),
            designation=designation,
        )
