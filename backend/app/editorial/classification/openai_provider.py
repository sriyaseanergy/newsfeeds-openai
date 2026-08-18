from collections import defaultdict

from pydantic import ValidationError

from app.ai.openai.client import OpenAIClient
from app.core.errors import ExternalServiceError
from app.core.settings import Settings, get_settings
from app.editorial.classification.models import (
    BatchedClassificationResponse,
    ClassificationBatchItem,
    ClassificationInput,
    EditorialClassification,
)
from app.editorial.classification.prompt_factory import PromptFactory
from app.editorial.classification.provider import ClassificationProvider
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class OpenAIClassificationProvider(ClassificationProvider):
    """
    Provider implementation that orchestrates classification via OpenAI.

    Flow (single):
        ClassificationInput
            ↓
        PromptFactory
            ↓
        OpenAIClient
            ↓
        EditorialClassification

    Flow (batch):
        ClassificationBatchItem[]
            ↓
        group by technology_domain
            ↓
        chunk by CLASSIFICATION_BATCH_SIZE
            ↓
        PromptFactory (batch payload)
            ↓
        OpenAIClient (BatchedClassificationResponse)
            ↓
        per-article fallback via classify() when needed
    """

    def __init__(
        self,
        openai_client: OpenAIClient | None = None,
        prompt_factory: PromptFactory | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.openai_client = openai_client or OpenAIClient(settings=self.settings)
        self.prompt_factory = prompt_factory or PromptFactory()
        self.batch_size = max(1, int(self.settings.classification_batch_size))

    def classify(
        self,
        classification_input: ClassificationInput,
    ) -> EditorialClassification:
        """Classify an article using the configured OpenAI model."""

        logger.info("OpenAI classification request started.")

        messages = self.prompt_factory.build_messages(classification_input)

        try:
            classification = self.openai_client.parse_response(
                model=self.settings.openai_classification_model,
                input=messages,
                text_format=EditorialClassification,
            )

            logger.info("OpenAI classification request completed.")
            return classification

        except ExternalServiceError:
            logger.exception("OpenAI classification request failed.")
            raise

    def classify_many(
        self,
        items: list[ClassificationBatchItem],
    ) -> dict[str, EditorialClassification]:
        if not items:
            return {}

        grouped: dict[str, list[ClassificationBatchItem]] = defaultdict(list)
        for item in items:
            domain_key = (item.classification_input.technology_domain or "").strip()
            grouped[domain_key].append(item)

        results: dict[str, EditorialClassification] = {}
        for domain_name, domain_items in grouped.items():
            for chunk_index, chunk in enumerate(
                self._chunk_items(domain_items, self.batch_size),
                start=1,
            ):
                batch_label = f"{domain_name or 'UNKNOWN'}#{chunk_index}"
                results.update(
                    self._classify_domain_batch(
                        domain_name=domain_name,
                        batch_label=batch_label,
                        chunk=chunk,
                    )
                )
        return results

    def _classify_domain_batch(
        self,
        *,
        domain_name: str,
        batch_label: str,
        chunk: list[ClassificationBatchItem],
    ) -> dict[str, EditorialClassification]:
        expected_ids = [item.article_id for item in chunk]
        id_to_item = {item.article_id: item for item in chunk}

        # Local stable IDs keep the model payload compact and unambiguous.
        local_id_to_article_id = {
            f"article_{index}": item.article_id
            for index, item in enumerate(chunk, start=1)
        }
        article_id_to_local_id = {
            article_id: local_id
            for local_id, article_id in local_id_to_article_id.items()
        }
        batch_payload = [
            (
                article_id_to_local_id[item.article_id],
                item.classification_input,
            )
            for item in chunk
        ]

        messages = self.prompt_factory.build_batch_messages(batch_payload)

        logger.info(
            "OpenAI batch classification request started "
            "(batch=%s domain=%s size=%s batch_size_limit=%s).",
            batch_label,
            domain_name or "UNKNOWN",
            len(chunk),
            self.batch_size,
        )

        try:
            batch_response = self.openai_client.parse_response(
                model=self.settings.openai_classification_model,
                input=messages,
                text_format=BatchedClassificationResponse,
            )
        except ExternalServiceError:
            logger.exception(
                "OpenAI batch classification request failed "
                "(batch=%s). Falling back to single-article classification "
                "for all %s articles in this batch.",
                batch_label,
                len(chunk),
            )
            return self._fallback_classify_items(
                items=chunk,
                batch_label=batch_label,
                reason="batch_request_failed",
            )

        results: dict[str, EditorialClassification] = {}
        seen_local_ids: set[str] = set()
        invalid_article_ids: list[str] = []

        for entry in batch_response.classifications:
            local_id = entry.article_id.strip()
            if local_id in seen_local_ids:
                logger.warning(
                    "Duplicate article_id '%s' in batch response (batch=%s); "
                    "keeping first valid result.",
                    local_id,
                    batch_label,
                )
                continue
            seen_local_ids.add(local_id)

            article_id = local_id_to_article_id.get(local_id)
            if article_id is None:
                logger.warning(
                    "Unknown article_id '%s' returned in batch response "
                    "(batch=%s); ignoring.",
                    local_id,
                    batch_label,
                )
                continue

            try:
                results[article_id] = entry.to_editorial_classification()
            except ValidationError as exc:
                invalid_article_ids.append(article_id)
                logger.warning(
                    "Batch classification validation failed "
                    "(batch=%s article_id=%s local_id=%s reason=%s). "
                    "Falling back to single-article classification.",
                    batch_label,
                    article_id,
                    local_id,
                    exc,
                )

        missing_article_ids = [
            article_id
            for article_id in expected_ids
            if article_id not in results and article_id not in invalid_article_ids
        ]
        for article_id in missing_article_ids:
            logger.warning(
                "Batch classification missing article "
                "(batch=%s article_id=%s local_id=%s). "
                "Falling back to single-article classification.",
                batch_label,
                article_id,
                article_id_to_local_id.get(article_id),
            )

        fallback_ids = missing_article_ids + invalid_article_ids
        if fallback_ids:
            fallback_items = [id_to_item[article_id] for article_id in fallback_ids]
            reason = "missing_or_invalid_in_batch_response"
            results.update(
                self._fallback_classify_items(
                    items=fallback_items,
                    batch_label=batch_label,
                    reason=reason,
                )
            )

        logger.info(
            "OpenAI batch classification request completed "
            "(batch=%s returned=%s fallback=%s).",
            batch_label,
            len(results) - len(fallback_ids),
            len(fallback_ids),
        )
        return results

    def _fallback_classify_items(
        self,
        *,
        items: list[ClassificationBatchItem],
        batch_label: str,
        reason: str,
    ) -> dict[str, EditorialClassification]:
        results: dict[str, EditorialClassification] = {}
        for item in items:
            logger.warning(
                "Single-article classification fallback "
                "(batch=%s article_id=%s reason=%s).",
                batch_label,
                item.article_id,
                reason,
            )
            try:
                results[item.article_id] = self.classify(item.classification_input)
            except Exception:
                logger.exception(
                    "Single-article classification fallback failed "
                    "(batch=%s article_id=%s reason=%s).",
                    batch_label,
                    item.article_id,
                    reason,
                )
        return results

    @staticmethod
    def _chunk_items(
        items: list[ClassificationBatchItem],
        batch_size: int,
    ) -> list[list[ClassificationBatchItem]]:
        return [
            items[index : index + batch_size]
            for index in range(0, len(items), batch_size)
        ]
