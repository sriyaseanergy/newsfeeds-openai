from pydantic import BaseModel, ConfigDict, Field


class DecisionDiagnosticSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=200)
    contribution: int


class DecisionDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signals: list[DecisionDiagnosticSignal] = Field(default_factory=list)
    final_score: int
    threshold: int
    include: bool
    rejection_reasons: list[str] = Field(default_factory=list)
