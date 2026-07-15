from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngestionRecordInput(BaseModel):
    external_id: str = Field(min_length=1, max_length=512)
    company: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    url: str = Field(min_length=1, max_length=2048)
    description: str | None = Field(default=None, max_length=500_000)
    raw_payload: dict = Field(default_factory=dict)


class IngestionRequest(BaseModel):
    provider: str = Field(pattern=r"^(fixture|greenhouse|lever)$")
    source_key: str = Field(min_length=1, max_length=255)
    records: list[IngestionRecordInput] = Field(min_length=1, max_length=1000)


class IngestionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    provider: str
    source_key: str
    status: str
    discovered_count: int
    created_count: int
    duplicate_count: int
    started_at: datetime
    completed_at: datetime | None
