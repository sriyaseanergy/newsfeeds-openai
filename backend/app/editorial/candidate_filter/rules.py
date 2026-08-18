from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from app.catalog.article.model import Article
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.models import CandidateFilterResult


class CandidateRule(ABC):
    @abstractmethod
    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        raise NotImplementedError


class MissingTitleRule(CandidateRule):
    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        if not (article.title or "").strip():
            return CandidateFilterResult(
                decision=CandidateDecision.SKIP,
                reason="missing_title",
            )
        return None


class MissingUrlRule(CandidateRule):
    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        if not (article.url or "").strip():
            return CandidateFilterResult(
                decision=CandidateDecision.SKIP,
                reason="missing_url",
            )
        return None


class EmptyContentRule(CandidateRule):
    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        summary = (article.summary or "").strip()
        content = (article.content or "").strip()
        if not summary and not content:
            return CandidateFilterResult(
                decision=CandidateDecision.SKIP,
                reason="empty_content",
            )
        return None


class EditorialWindowRule(CandidateRule):
    def __init__(self, window_days: int | None = None):
        self.window_days = window_days

    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        if self.window_days is None:
            return None

        published_at = article.published_at
        if published_at is None:
            return None

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        cutoff = datetime.now(UTC) - timedelta(days=self.window_days)
        if published_at < cutoff:
            return CandidateFilterResult(
                decision=CandidateDecision.SKIP,
                reason="outside_editorial_window",
            )
        return None

class AlreadyProcessedRule(CandidateRule):
    def evaluate(self, article: Article) -> CandidateFilterResult | None:
        if article.is_processed:
            return CandidateFilterResult(
                decision=CandidateDecision.SKIP,
                reason="already_processed",
            )
        return None