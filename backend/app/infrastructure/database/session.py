from collections.abc import Generator

from app.infrastructure.config.settings import get_settings
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()

if not settings.database_url:
    raise ValueError("DATABASE_URL is not configured.")


def _normalize_database_url(database_url: str) -> str:
    """
    Keep sync SQLAlchemy compatible with common async URL variants.
    """
    url = make_url(database_url)

    if url.drivername == "postgresql+asyncpg":
        return str(url.set(drivername="postgresql+psycopg"))

    return database_url


engine = create_engine(_normalize_database_url(settings.database_url), pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

