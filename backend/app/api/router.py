from app.api.auth.router import router as auth_router
from app.catalog.article.router import router as article_router
from app.catalog.email_recipient.router import router as email_recipient_router
from app.catalog.feed.router import router as feed_router
from app.catalog.technology_domain.router import router as technology_domain_router
from app.catalog.user_category_preference.router import (
    router as user_category_preference_router,
)
from app.ingestion.router import router as ingestion_router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(user_category_preference_router)
api_router.include_router(technology_domain_router)
api_router.include_router(feed_router)
api_router.include_router(article_router)
api_router.include_router(email_recipient_router)
api_router.include_router(ingestion_router)
