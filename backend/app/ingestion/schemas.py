from app.catalog.technology_domain.model import TechnologyDomainSchedule
from app.ingestion.models import IngestionResult
from pydantic import BaseModel, ConfigDict


class IngestionRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schedule: TechnologyDomainSchedule


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[IngestionResult]

