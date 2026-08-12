from pydantic import BaseModel, ConfigDict, Field


class EditorialDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_in_newsletter: bool
    priority: str = Field(min_length=1, max_length=32)
    rationale: str = Field(min_length=1, max_length=500)
