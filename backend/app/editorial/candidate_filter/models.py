from pydantic import BaseModel, ConfigDict, Field

from app.editorial.candidate_filter.enums import CandidateDecision


class CandidateFilterResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: CandidateDecision
    reason: str = Field(min_length=1, max_length=255)

