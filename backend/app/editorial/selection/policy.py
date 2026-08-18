from typing import Protocol

from app.editorial.classification.enums import Actionability, ArticleType, Audience, Severity
from app.editorial.classification.models import EditorialClassification
from app.editorial.selection.models import SelectionResult, SelectionTier


class EntityWatchlist(Protocol):
    """Pluggable relevance source. No-op until you wire a real implementation."""

    def relevance_points(self, classification: EditorialClassification) -> int:
        ...


class NullWatchlist:
    """Default no-op watchlist — always contributes 0 points."""

    def relevance_points(self, classification: EditorialClassification) -> int:
        return 0


class SelectionPolicy:
    """
    Ranks classified articles per domain and takes the top-K per group.
    Never gates on a scalar threshold — miscalibration only reorders,
    it never flips a good article to "excluded".
    """

    _MIN_CONFIDENCE_FLOOR = 0.3  # true junk filter, not a ranking cutoff

    _SEVERITY_POINTS = {
        Severity.NONE: 0,
        Severity.LOW: 10,
        Severity.MEDIUM: 30,
        Severity.HIGH: 55,
        Severity.CRITICAL: 70,
    }
    _ACTIONABILITY_POINTS = {
        Actionability.INFORMATIONAL: 0,
        Actionability.MONITOR: 15,
        Actionability.ACTION_RECOMMENDED: 50,
        Actionability.IMMEDIATE_ACTION: 70,
    }
    _AUDIENCE_FIT_POINTS = {
        Audience.AI: 10,
        Audience.ENGINEERING: 10,
        Audience.LEADERSHIP: 10,
        Audience.SECURITY: 10,
        Audience.GENERAL: 0,
    }

    # domain -> {article_type (or None = no grouping) : slot count}
    _DOMAIN_SLOT_CONFIG: dict[str, dict[ArticleType | None, int]] = {
        "SECURITY": {None: 5},
        "EXPERT_CONTEXT": {None: 2},
        "AI": {
            ArticleType.RESEARCH: 2,
            ArticleType.RELEASE: 1,
            ArticleType.NEWS: 1,
            ArticleType.BLOG: 1,
        },
        "ML": {
            ArticleType.RESEARCH: 2,
            ArticleType.RELEASE: 1,
            ArticleType.NEWS: 1,
            ArticleType.BLOG: 1,
        },
    }
    _DEFAULT_SLOTS = {
        ArticleType.RESEARCH: 1,
        ArticleType.RELEASE: 1,
        ArticleType.NEWS: 1,
    }

    def __init__(self, watchlist: EntityWatchlist | None = None) -> None:
        self.watchlist = watchlist or NullWatchlist()

    def select_for_domain(
        self,
        domain_name: str,
        classified: list[tuple[str, EditorialClassification]],
    ) -> dict[str, SelectionResult]:
        results: dict[str, SelectionResult] = {}
        viable: list[tuple[str, EditorialClassification]] = []

        for article_id, classification in classified:
            if classification.confidence < self._MIN_CONFIDENCE_FLOOR:
                results[article_id] = SelectionResult(
                    article_id=article_id,
                    tier=SelectionTier.DISCARD,
                    rank_score=0,
                    group_key=f"{domain_name}:LOW_CONFIDENCE",
                )
            else:
                viable.append((article_id, classification))

        slot_config = self._DOMAIN_SLOT_CONFIG.get(domain_name, self._DEFAULT_SLOTS)

        for group_type, slots in slot_config.items():
            candidates = [
                (article_id, classification)
                for article_id, classification in viable
                if group_type is None or classification.article_type == group_type
            ]
            ranked = sorted(
                candidates,
                key=lambda item: (self._rank_score(item[1]), item[1].confidence),
                reverse=True,
            )
            group_key = f"{domain_name}:{group_type.value if group_type else 'ALL'}"
            for index, (article_id, classification) in enumerate(ranked):
                tier = (
                    SelectionTier.SELECTED_FOR_ENRICHMENT
                    if index < slots
                    else SelectionTier.SHOWN_ON_UI
                )
                results[article_id] = SelectionResult(
                    article_id=article_id,
                    tier=tier,
                    rank_score=self._rank_score(classification),
                    rank_within_group=index + 1,
                    group_key=group_key,
                )

        for article_id, classification in viable:
            results.setdefault(
                article_id,
                SelectionResult(
                    article_id=article_id,
                    tier=SelectionTier.SHOWN_ON_UI,
                    rank_score=self._rank_score(classification),
                    group_key=f"{domain_name}:UNGROUPED",
                ),
            )
        return results

    def _rank_score(self, classification: EditorialClassification) -> int:
        return (
            self._SEVERITY_POINTS[classification.severity]
            + self._ACTIONABILITY_POINTS[classification.actionability]
            + self._AUDIENCE_FIT_POINTS[classification.audience]
            + self.watchlist.relevance_points(classification)
        )
