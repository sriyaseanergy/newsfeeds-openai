from collections.abc import Sequence
from typing import Any

import feedparser
from app.catalog.feed.model import Feed


class RSSClient:
    def fetch_feed_entries(self, feed: Feed) -> Sequence[dict[str, Any]]:
        parsed = feedparser.parse(feed.url)

        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", []):
            exception = getattr(parsed, "bozo_exception", None)
            message = (
                str(exception) if exception is not None else "Invalid feed payload."
            )
            raise ValueError(f"Failed to parse feed '{feed.url}': {message}")

        return [dict(entry) for entry in parsed.entries]
