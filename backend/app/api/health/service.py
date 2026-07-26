from app.api.health.schemas import HealthResponse
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import SessionLocal
from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthService:
    @staticmethod
    def get_health(_db: Session | None = None) -> HealthResponse:
        settings = get_settings()
        db = None

        try:
            db = SessionLocal()
            db.execute(text("SELECT 1;"))
            database_status = "connected"
        except Exception:
            database_status = "disconnected"
        finally:
            if db is not None:
                db.close()

        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            database=database_status,
        )
