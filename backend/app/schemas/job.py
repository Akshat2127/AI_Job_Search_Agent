from datetime import datetime
from pydantic import BaseModel, Field

class JobCreate(BaseModel):
    company: str
    title: str
    location: str | None = None
    remote_type: str | None = None
    url: str
    source: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None

class JobOut(JobCreate):
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

    class Config:
        from_attributes = True

class DecisionUpdate(BaseModel):
    decision: str = Field(pattern="^(approve|maybe|skip|new|applied|interview|offer|rejected)$")

class JobFilters(BaseModel):
    min_score: int | None = None
    decision: str | None = None
    q: str | None = None
