from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.mapper import ArticleMapper
from app.ingestion.models import IngestionResult, NormalizedArticleData
from app.ingestion.json_fetcher import JsonFeedAcquirer
from app.ingestion.json_client import JsonFeedClient
from app.ingestion.json_mapper import JsonArticleMapper
from app.ingestion.rss_fetcher import RSSFeedAcquirer
from app.ingestion.schemas import IngestionRunRequest, IngestionRunResponse
from app.ingestion.rss_client import RSSClient
from app.ingestion.service import IngestionService

__all__ = [
    "AcquisitionFactory",
    "ArticleMapper",
    "JsonFeedAcquirer",
    "JsonFeedClient",
    "JsonArticleMapper",
    "Crawl4AIFetcher",
    "FeedAcquirer",
    "FeedAcquisitionResult",
    "IngestionRunRequest",
    "IngestionRunResponse",
    "IngestionResult",
    "IngestionService",
    "NormalizedArticleData",
    "RSSFeedAcquirer",
    "RSSClient",
]
