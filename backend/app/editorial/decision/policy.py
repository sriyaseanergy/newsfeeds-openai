from abc import ABC, abstractmethod

from app.editorial.classification.models import EditorialClassification
from app.editorial.decision.diagnostics import (
    DecisionDiagnosticSignal,
    DecisionDiagnostics,
)
from app.editorial.decision.models import EditorialDecision


class EditorialDecisionPolicy(ABC):
    @abstractmethod
    def decide(self, classification: EditorialClassification) -> EditorialDecision:
        """Produce pre-enrichment include/priority/rationale decision."""

    @abstractmethod
    def build_diagnostics(
        self,
        classification: EditorialClassification,
        decision: EditorialDecision,
    ) -> DecisionDiagnostics:
        """Build score-level diagnostics for the provided decision."""


class DefaultEditorialDecisionPolicy(EditorialDecisionPolicy):
    """
    Default policy preserving current decision behavior exactly.
    """

    _INCLUSION_THRESHOLD = 70
    _SEVERITY_INCLUDE_POINTS = 70
    _ACTIONABILITY_INCLUDE_POINTS = 70

    def decide(self, classification: EditorialClassification) -> EditorialDecision:
        high_risk = self._is_high_risk(classification)
        actionable = self._is_actionable(classification)

        include = high_risk or actionable
        priority = "HIGH" if include else "NORMAL"
        if include:
            rationale = "Included by decision scoring; awaiting enrichment details."
        else:
            rationale = "Useful context, but not urgent enough for inclusion."

        return EditorialDecision(
            include_in_newsletter=include,
            priority=priority,
            rationale=rationale,
        )

    def build_diagnostics(
        self,
        classification: EditorialClassification,
        decision: EditorialDecision,
    ) -> DecisionDiagnostics:
        high_risk = self._is_high_risk(classification)
        actionable = self._is_actionable(classification)

        severity_points = self._SEVERITY_INCLUDE_POINTS if high_risk else 0
        actionability_points = self._ACTIONABILITY_INCLUDE_POINTS if actionable else 0
        final_score = severity_points + actionability_points

        rejection_reasons: list[str] = []
        if not decision.include_in_newsletter:
            if not high_risk:
                rejection_reasons.append(
                    f"Severity '{classification.severity.value}' is below include level (High/Critical)."
                )
            if not actionable:
                rejection_reasons.append(
                    "Actionability is not include-triggering "
                    f"('{classification.actionability.value}'; expected Action Recommended/Immediate Action)."
                )

        return DecisionDiagnostics(
            signals=[
                DecisionDiagnosticSignal(
                    name="Severity",
                    value=classification.severity.value,
                    contribution=severity_points,
                ),
                DecisionDiagnosticSignal(
                    name="Actionability",
                    value=classification.actionability.value,
                    contribution=actionability_points,
                ),
            ],
            final_score=final_score,
            threshold=self._INCLUSION_THRESHOLD,
            include=decision.include_in_newsletter,
            rejection_reasons=rejection_reasons,
        )

    @staticmethod
    def _is_high_risk(classification: EditorialClassification) -> bool:
        return classification.severity.value in {"High", "Critical"}

    @staticmethod
    def _is_actionable(classification: EditorialClassification) -> bool:
        return classification.actionability.value in {
            "Action Recommended",
            "Immediate Action",
        }
