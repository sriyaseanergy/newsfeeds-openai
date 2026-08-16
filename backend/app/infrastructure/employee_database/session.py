from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from app.infrastructure.config.settings import get_settings
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()


class EmployeeDatabaseConfigurationError(Exception):
    """MyWork SQL Server is missing, misconfigured, or unavailable at startup."""


def _employee_db_config_error(exc: Exception) -> EmployeeDatabaseConfigurationError:
    if isinstance(exc, ValueError):
        return EmployeeDatabaseConfigurationError(str(exc))
    if isinstance(exc, ModuleNotFoundError):
        return EmployeeDatabaseConfigurationError(
            "pyodbc is not installed in the API runtime. Install pyodbc and "
            "Microsoft ODBC Driver for SQL Server."
        )
    return EmployeeDatabaseConfigurationError(
        "MyWork database is not configured correctly. "
        "Check MYWORK_DATABASE_URL and the SQL Server ODBC driver."
    )


@lru_cache
def get_employee_engine() -> Engine:
    database_url = settings.mywork_database_url.strip()
    if not database_url:
        msg = "MYWORK_DATABASE_URL is not configured."
        raise ValueError(msg)
    try:
        return create_engine(database_url, pool_pre_ping=True)
    except Exception as exc:
        raise _employee_db_config_error(exc) from exc


@lru_cache
def get_employee_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_employee_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


def open_employee_session() -> Session:
    try:
        session_factory = get_employee_session_factory()
    except EmployeeDatabaseConfigurationError:
        raise
    except Exception as exc:
        raise _employee_db_config_error(exc) from exc
    return session_factory()


def get_employee_db() -> Generator[Session, None, None]:
    try:
        db = open_employee_session()
    except EmployeeDatabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    try:
        yield db
    finally:
        db.close()
