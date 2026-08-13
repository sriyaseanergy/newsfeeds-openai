from contextlib import asynccontextmanager

from app.api.router import api_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging import configure_logging, get_logger
from app.scheduling.scheduler import create_scheduler
from fastapi import FastAPI

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler(settings)
    if settings.scheduler_enabled:
        scheduler.start()
        logger.info(
            "Digest scheduler started (IST daily=%s weekly=%s %s).",
            settings.daily_digest_time,
            settings.weekly_digest_day,
            settings.weekly_digest_time,
        )
    else:
        logger.info("Digest scheduler disabled via scheduler_enabled=false.")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Digest scheduler stopped.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    root_path=settings.root_path,
    lifespan=lifespan,
)

app.include_router(api_router)
logger.info("Application startup completed.")
