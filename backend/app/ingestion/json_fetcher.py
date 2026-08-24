from app.catalog.feed.model import Feed
from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.json_client import JsonFeedClient
from app.ingestion.json_mapper import JsonArticleMapper
from pydantic import ValidationError


class JsonFeedAcquirer(FeedAcquirer):
    def __init__(
        self,
        json_client: JsonFeedClient | None = None,
        article_mapper: JsonArticleMapper | None = None,
    ) -> None:
        self.json_client = json_client or JsonFeedClient()
        self.article_mapper = article_mapper or JsonArticleMapper()

    def acquire(
        self,
        feed: Feed,
        known_urls: set[str] | None = None,
    ) -> FeedAcquisitionResult:
        items = self.json_client.fetch_feed_items(feed)
        result = FeedAcquisitionResult(fetched_count=len(items))
        known = {url.strip().lower() for url in (known_urls or set()) if url.strip()}

        for item in items:
            try:
                article_data = self.article_mapper.map_item_to_article_data(feed, item)
            except (ValidationError, ValueError) as exc:
                result.errors.append(f"Item skipped: {exc}")
                continue
            except Exception as exc:
                result.errors.append(f"Item mapping failed: {exc}")
                continue

            if known and article_data.url.strip().lower() in known:
                continue
            result.articles.append(article_data)

        return result
