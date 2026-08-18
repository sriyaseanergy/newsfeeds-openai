from app.ai.openai.client import OpenAIClient
from app.core.errors import ExternalServiceError
from app.core.settings import Settings, get_settings
from app.editorial.enrichment.models import ClassifiedArticle, EnrichedArticle
from app.editorial.enrichment.prompts import build_enrichment_messages
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


def enrich_article(
    classified_article: ClassifiedArticle,
    *,
    openai_client: OpenAIClient | None = None,
    settings: Settings | None = None,
) -> EnrichedArticle:
    """
    Enrich a classified article using the configured OpenAI model.

    Flow:
        ClassifiedArticle
            ↓
        build_enrichment_messages
            ↓
        OpenAIClient.parse_response
            ↓
        EnrichedArticle
    """

    resolved_settings = settings or get_settings()
    client = openai_client or OpenAIClient(settings=resolved_settings)
    messages = build_enrichment_messages(classified_article)

    logger.info("OpenAI enrichment request started.")

    try:
        enrichment = client.parse_response(
            model=resolved_settings.openai_enrichment_model,
            input=messages,
            text_format=EnrichedArticle,
        )
        logger.info("OpenAI enrichment request completed.")
        return enrichment

    except ExternalServiceError:
        logger.exception("OpenAI enrichment request failed.")
        raise
