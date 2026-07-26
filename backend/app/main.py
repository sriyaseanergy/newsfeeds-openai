from app.api.router import api_router
from app.infrastructure.config.settings import get_settings
from fastapi import FastAPI

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(api_router)
