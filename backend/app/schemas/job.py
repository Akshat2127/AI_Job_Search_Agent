from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class JobCreate(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    location: str | None = None
    remote_type: str | None = None
    url: str = Field(min_length=1, max_length=2048)
    source: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None

    @field_validator("company", "title")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("url")
    @classmethod
    def validate_public_web_url_shape(cls, value: str) -> str:
        """Reject active-content and credential-bearing links at the API boundary.

        This is intentionally only syntactic validation. Any future server-side fetch
        must additionally resolve and block private/link-local network destinations.
        """
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("must be an absolute HTTP(S) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("must not contain embedded credentials")
        return value

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value: float | None, info: ValidationInfo) -> float | None:
        minimum = info.data.get("salary_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("must be greater than or equal to salary_min")
        return value


class JobOut(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fit_score: int
    score_reason: str | None = None
    resume_variant: str | None = None
    cover_letter: str | None = None
    recruiter_message: str | None = None
    decision: str
    status: str
    created_at: datetime
    updated_at: datetime


class DecisionUpdate(BaseModel):
    decision: str = Field(pattern="^(approve|maybe|skip|new|applied|interview|offer|rejected)$")


class CandidateDecisionUpdate(BaseModel):
    decision: str = Field(pattern="^(approve|maybe|skip|new)$")


class CandidateJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    title: str
    location: str | None
    url: str
    source: str | None
    description: str | None
    decision: str
    status: str
    created_at: datetime
    updated_at: datetime


class CandidateJobPage(BaseModel):
    items: list[CandidateJobOut]
    total: int
    limit: int
    offset: int


class JobProvenanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    source_key: str
    external_id: str
    source_url: str
    first_seen_at: datetime
    last_seen_at: datetime


class JobFilters(BaseModel):
    min_score: int | None = None
    decision: str | None = None
    q: str | None = None
