from abc import ABC, abstractmethod

from app.editorial.classification.enums import Actionability, ArticleType, Audience, Severity
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


class AIEditorialDecisionPolicy(EditorialDecisionPolicy):
    """
    AI/newsletter-oriented policy that combines urgency and notability signals.
    """

    _INCLUSION_THRESHOLD = 40
    _SEVERITY_INCLUDE_POINTS = 70
    _ACTIONABILITY_INCLUDE_POINTS = 70
    _NOTABILITY_RELEASE_POINTS = 40
    _NOTABILITY_RESEARCH_POINTS = 25
    _NOTABILITY_BLOG_NEWS_POINTS = 20
    _MIN_CONFIDENCE_FOR_BLOG_NEWS = 0.6

    def decide(self, classification: EditorialClassification) -> EditorialDecision:
        severity_points = (
            self._SEVERITY_INCLUDE_POINTS
            if self._is_high_risk(classification)
            else 0
        )
        actionability_points = (
            self._ACTIONABILITY_INCLUDE_POINTS
            if self._is_actionable(classification)
            else 0
        )
        notability_points = self._notability_points(classification)
        final_score = severity_points + actionability_points + notability_points
        include = final_score >= self._INCLUSION_THRESHOLD
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
        notability_points = self._notability_points(classification)
        severity_points = self._SEVERITY_INCLUDE_POINTS if high_risk else 0
        actionability_points = self._ACTIONABILITY_INCLUDE_POINTS if actionable else 0
        final_score = severity_points + actionability_points + notability_points

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
            if notability_points == 0:
                rejection_reasons.append(
                    "Notability did not contribute (expected Release, Research, or Blog/News "
                    "with audience AI/Leadership/Engineering and confidence >= 0.6)."
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
                DecisionDiagnosticSignal(
                    name="Notability",
                    value=(
                        f"type={classification.article_type.value}, "
                        f"audience={classification.audience.value}, "
                        f"confidence={classification.confidence:.2f}"
                    ),
                    contribution=notability_points,
                ),
            ],
            final_score=final_score,
            threshold=self._INCLUSION_THRESHOLD,
            include=decision.include_in_newsletter,
            rejection_reasons=rejection_reasons,
        )

    @staticmethod
    def _is_high_risk(classification: EditorialClassification) -> bool:
        return classification.severity in {Severity.HIGH, Severity.CRITICAL}

    @staticmethod
    def _is_actionable(classification: EditorialClassification) -> bool:
        return classification.actionability in {
            Actionability.ACTION_RECOMMENDED,
            Actionability.IMMEDIATE_ACTION,
        }

    def _notability_points(self, classification: EditorialClassification) -> int:
        if classification.article_type == ArticleType.RELEASE:
            return self._NOTABILITY_RELEASE_POINTS
        if classification.article_type == ArticleType.RESEARCH:
            return self._NOTABILITY_RESEARCH_POINTS
        if (
            classification.article_type in {ArticleType.BLOG, ArticleType.NEWS}
            and classification.audience
            in {Audience.AI, Audience.LEADERSHIP, Audience.ENGINEERING}
            and classification.confidence >= self._MIN_CONFIDENCE_FOR_BLOG_NEWS
        ):
            return self._NOTABILITY_BLOG_NEWS_POINTS
        return 0
