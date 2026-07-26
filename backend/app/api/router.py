from app.api.health.router import router as health_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health_router)
