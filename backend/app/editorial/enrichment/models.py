from pydantic import BaseModel, ConfigDict, Field


class EditorialEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key_points: list[str] = Field(default_factory=list)
    business_impact: str = Field(min_length=1, max_length=400)
    recommended_action: str = Field(min_length=1, max_length=400)
