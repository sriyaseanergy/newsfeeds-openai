from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SelectionTier(str, Enum):
    SELECTED_FOR_ENRICHMENT = "SELECTED_FOR_ENRICHMENT"
    SHOWN_ON_UI = "SHOWN_ON_UI"
    DISCARD = "DISCARD"


class SelectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_id: str = Field(min_length=1, max_length=64)
    tier: SelectionTier
    rank_score: int
    group_key: str = Field(min_length=1, max_length=128)
    rank_within_group: int | None = Field(default=None, ge=1)
