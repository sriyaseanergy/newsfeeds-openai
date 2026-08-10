from abc import ABC, abstractmethod

from app.ai.openai.client import OpenAIClient
from app.core.settings import Settings, get_settings
from app.editorial.classification.models import EditorialClassification
from app.editorial.enrichment.models import EditorialEnrichment
from app.editorial.enrichment.prompt import build_enrichment_prompt
from app.ingestion.models import NormalizedArticleData


class EditorialEnrichmentProvider(ABC):
    @abstractmethod
    def enrich(
        self,
        article: NormalizedArticleData,
        classification: EditorialClassification,
    ) -> EditorialEnrichment:
        raise NotImplementedError


class OpenAIEditorialEnrichmentProvider(EditorialEnrichmentProvider):
    def __init__(
        self,
        openai_client: OpenAIClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.openai_client = openai_client or OpenAIClient(settings=self.settings)

    def enrich(
        self,
        article: NormalizedArticleData,
        classification: EditorialClassification,
    ) -> EditorialEnrichment:
        prompt = build_enrichment_prompt(article, classification)
        return self.openai_client.parse_response(
            model=self.openai_client.enrichment_model,
            input=prompt,
            text_format=EditorialEnrichment,
        )
