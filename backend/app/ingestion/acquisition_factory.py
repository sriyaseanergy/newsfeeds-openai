from app.catalog.feed.model import Feed, FetchKind
from app.ingestion.acquisition import FeedAcquirer
from app.ingestion.crawl4ai_fetcher import Crawl4AIFetcher
from app.ingestion.rss_fetcher import RSSFeedAcquirer


class AcquisitionFactory:
    def __init__(
        self,
        rss_acquirer: FeedAcquirer | None = None,
        crawl_acquirer: FeedAcquirer | None = None,
    ):
        self.rss_acquirer = rss_acquirer or RSSFeedAcquirer()
        self.crawl_acquirer = crawl_acquirer or Crawl4AIFetcher()

    def for_feed(self, feed: Feed) -> FeedAcquirer:
        if feed.fetch_kind == FetchKind.CRAWL:
            return self.crawl_acquirer
        return self.rss_acquirer
