from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from app.api.router import api_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging import configure_logging, get_logger
from app.notifications.email.graph_auth import (
    ensure_graph_delegated_auth,
    graph_login_base_url,
)
from app.notifications.email.oauth_routes import router as graph_oauth_router
from app.scheduling.scheduler import create_scheduler
from fastapi import FastAPI

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


def _log_graph_login_url_if_needed(resolved_settings) -> None:
    token_path = Path(resolved_settings.graph_token_cache_path)
    if token_path.exists():
        return

    base_url = graph_login_base_url(resolved_settings)
    logger.warning("Sign in at: %s/login", base_url)

    redirect_uri = resolved_settings.redirect_uri.strip()
    if not redirect_uri:
        logger.warning(
            "REDIRECT_URI is not set. Configure REDIRECT_URI to match the "
            "callback route (/callback) and your Azure app registration."
        )
        return

    parsed = urlparse(redirect_uri)
    if parsed.path.rstrip("/") != "/callback":
        logger.warning(
            "REDIRECT_URI path is %s but the OAuth callback route is /callback. "
            "Azure app registration must register REDIRECT_URI exactly as "
            "configured in the environment.",
            parsed.path or "/",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Employee sign-in audience AZURE_AUTH_CLIENT_ID=%s",
        settings.azure_auth_client_id or "(not set)",
    )
    ensure_graph_delegated_auth(settings)
    _log_graph_login_url_if_needed(settings)
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
app.include_router(graph_oauth_router)
logger.info("Application startup completed.")
