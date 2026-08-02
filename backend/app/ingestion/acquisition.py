from abc import ABC, abstractmethod

from app.catalog.feed.model import Feed
from app.ingestion.models import NormalizedArticleData
from pydantic import BaseModel, ConfigDict, Field


class FeedAcquisitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fetched_count: int = Field(default=0, ge=0)
    articles: list[NormalizedArticleData] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FeedAcquirer(ABC):
    @abstractmethod
    def acquire(self, feed: Feed) -> FeedAcquisitionResult:
        """Fetch articles from a feed and normalize them."""
