from typing import Protocol

from app.editorial.classification.models import EditorialClassification
from app.editorial.decision.diagnostics import DecisionDiagnostics
from app.editorial.decision.models import EditorialDecision
from app.editorial.decision.policy import (
    DefaultEditorialDecisionPolicy,
    EditorialDecisionPolicy,
)


class _HasRecommendedAction(Protocol):
    recommended_action: str


class EditorialDecisionEngine:
    def __init__(self, policy: EditorialDecisionPolicy | None = None):
        self.policy = policy or DefaultEditorialDecisionPolicy()

    def decide(self, classification: EditorialClassification) -> EditorialDecision:
        return self.policy.decide(classification)

    def decide_pre_enrichment(
        self,
        classification: EditorialClassification,
    ) -> EditorialDecision:
        # Backward-compatible alias used by existing runner flow.
        return self.decide(classification)

    @staticmethod
    def finalize_with_enrichment(
        decision: EditorialDecision,
        enrichment: _HasRecommendedAction,
    ) -> EditorialDecision:
        if not decision.include_in_newsletter:
            return decision
        return decision.model_copy(update={"rationale": enrichment.recommended_action})

    def build_diagnostics(
        self,
        classification: EditorialClassification,
        decision: EditorialDecision,
    ) -> DecisionDiagnostics:
        return self.policy.build_diagnostics(classification, decision)
