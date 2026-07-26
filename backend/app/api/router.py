from app.api.health.router import router as health_router
from app.catalog.article.router import router as article_router
from app.catalog.feed.router import router as feed_router
from app.catalog.technology_domain.router import router as technology_domain_router
from app.ingestion.router import router as ingestion_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(technology_domain_router)
api_router.include_router(feed_router)
api_router.include_router(article_router)
api_router.include_router(ingestion_router)
