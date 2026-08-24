from app.catalog.feed.model import Feed, FetchKind
from app.ingestion.acquisition import FeedAcquirer
from app.ingestion.crawl4ai_fetcher import Crawl4AIFetcher
from app.ingestion.json_fetcher import JsonFeedAcquirer
from app.ingestion.rss_fetcher import RSSFeedAcquirer


class AcquisitionFactory:
    def __init__(
        self,
        rss_acquirer: FeedAcquirer | None = None,
        crawl_acquirer: FeedAcquirer | None = None,
        json_acquirer: FeedAcquirer | None = None,
    ):
        self.rss_acquirer = rss_acquirer or RSSFeedAcquirer()
        self.crawl_acquirer = crawl_acquirer or Crawl4AIFetcher()
        self.json_acquirer = json_acquirer or JsonFeedAcquirer()

    def for_feed(self, feed: Feed) -> FeedAcquirer:
        if feed.fetch_kind == FetchKind.CRAWL:
            return self.crawl_acquirer
        if feed.fetch_kind == FetchKind.JSON_API:
            return self.json_acquirer
        return self.rss_acquirer
