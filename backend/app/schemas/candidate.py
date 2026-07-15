from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    headline: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=10000)
    years_experience: float | None = Field(default=None, ge=0, le=80)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class CandidateUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    headline: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=10000)
    years_experience: float | None = Field(default=None, ge=0, le=80)
    is_archived: bool | None = None


class CandidateOut(CandidateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class PreferenceInput(BaseModel):
    target_roles: list[str] = Field(default_factory=list, max_length=50)
    preferred_locations: list[str] = Field(default_factory=list, max_length=50)
    remote_preferences: list[str] = Field(default_factory=list, max_length=10)
    salary_floor: float | None = Field(default=None, ge=0)
    excluded_employers: list[str] = Field(default_factory=list, max_length=100)
    excluded_titles: list[str] = Field(default_factory=list, max_length=100)
    keyword_preferences: list[str] = Field(default_factory=list, max_length=100)
    work_authorization: str | None = Field(default=None, max_length=255)
    sponsorship_required: bool | None = None

    @field_validator(
        "target_roles",
        "preferred_locations",
        "remote_preferences",
        "excluded_employers",
        "excluded_titles",
        "keyword_preferences",
    )
    @classmethod
    def clean_list(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class PreferenceOut(PreferenceInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    updated_at: datetime


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    years_experience: float | None = Field(default=None, ge=0, le=80)


class SkillOut(SkillCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmed: bool
    source: str


class ExperienceCreate(BaseModel):
    employer: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    description: str | None = Field(default=None, max_length=20000)


class ExperienceOut(ExperienceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmed: bool
    source: str
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=20000)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")


class ProjectOut(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmed: bool
    source: str
    created_at: datetime


class EducationCreate(BaseModel):
    institution: str = Field(min_length=1, max_length=255)
    degree: str | None = Field(default=None, max_length=255)
    field_of_study: str | None = Field(default=None, max_length=255)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")


class EducationOut(EducationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmed: bool
    source: str


class CertificationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    issuer: str | None = Field(default=None, max_length=255)
    issued_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    expires_date: str | None = Field(default=None, pattern=r"^\d{4}(-\d{2})?$")
    credential_id: str | None = Field(default=None, max_length=255)


class CertificationOut(CertificationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmed: bool
    source: str


class AnswerCreate(BaseModel):
    question_key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    answer: str = Field(min_length=1, max_length=10000)
    sensitive: bool = False
    require_confirmation_each_time: bool = False


class AnswerOut(AnswerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    updated_at: datetime


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    original_filename: str
    media_type: str
    byte_size: int
    sha256: str
    extracted_text: str
    review_status: str
    label: str | None
    version_number: int
    is_master: bool
    is_archived: bool
    created_at: datetime


class ResumeReviewUpdate(BaseModel):
    review_status: str = Field(pattern=r"^(approved|rejected|needs_review)$")
    extracted_text: str | None = Field(default=None, max_length=200000)
    label: str | None = Field(default=None, max_length=255)
    is_master: bool | None = None
    is_archived: bool | None = None
