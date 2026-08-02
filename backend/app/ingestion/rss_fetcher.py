from app.catalog.feed.model import Feed
from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.mapper import ArticleMapper
from app.ingestion.rss_client import RSSClient
from pydantic import ValidationError


class RSSFeedAcquirer(FeedAcquirer):
    def __init__(
        self,
        rss_client: RSSClient | None = None,
        article_mapper: ArticleMapper | None = None,
    ):
        self.rss_client = rss_client or RSSClient()
        self.article_mapper = article_mapper or ArticleMapper()

    def acquire(self, feed: Feed) -> FeedAcquisitionResult:
        entries = self.rss_client.fetch_feed_entries(feed)
        result = FeedAcquisitionResult(fetched_count=len(entries))

        for entry in entries:
            try:
                article_data = self.article_mapper.map_entry_to_article_data(feed, entry)
            except (ValidationError, ValueError) as exc:
                result.errors.append(f"Entry skipped: {exc}")
                continue
            except Exception as exc:
                result.errors.append(f"Entry mapping failed: {exc}")
                continue
            result.articles.append(article_data)

        return result
