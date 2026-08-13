from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from app.infrastructure.config.settings import get_settings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()


@lru_cache
def get_employee_engine() -> Engine:
    database_url = settings.mywork_database_url.strip()
    if not database_url:
        msg = "MYWORK_DATABASE_URL is not configured."
        raise ValueError(msg)
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_employee_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_employee_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_employee_db() -> Generator[Session, None, None]:
    session_factory = get_employee_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
