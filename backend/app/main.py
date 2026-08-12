from app.api.router import api_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging import configure_logging, get_logger
from fastapi import FastAPI

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(api_router)
logger.info("Application startup completed.")
