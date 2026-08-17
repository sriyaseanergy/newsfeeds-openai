from collections.abc import Sequence

from app.catalog.article.model import Article
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.models import CandidateFilterResult
from app.editorial.candidate_filter.rules import (
    CandidateRule,
    EditorialWindowRule,
    EmptyContentRule,
    MissingTitleRule,
    MissingUrlRule,
    AlreadyProcessedRule,
)


class CandidateFilterService:
    def __init__(
        self,
        rules: Sequence[CandidateRule] | None = None,
        editorial_window_days: int | None = None,
    ):
        self.rules = list(rules) if rules is not None else [
            MissingTitleRule(),
            MissingUrlRule(),
            EmptyContentRule(),
            AlreadyProcessedRule(),
            EditorialWindowRule(window_days=editorial_window_days),
        ]

    def evaluate(self, article: Article) -> CandidateFilterResult:
        for rule in self.rules:
            result = rule.evaluate(article)
            if result is not None:
                return result

        return CandidateFilterResult(
            decision=CandidateDecision.CLASSIFY,
            reason="passed",
        )

