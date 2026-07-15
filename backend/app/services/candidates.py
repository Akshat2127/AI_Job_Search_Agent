from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.candidate import (
    ApplicationAnswer,
    CandidatePreference,
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    EmploymentExperience,
    ProjectExperience,
    Resume,
)
from backend.app.models.identity import User
from backend.app.schemas.candidate import (
    AnswerCreate,
    CandidateCreate,
    CandidateUpdate,
    CertificationCreate,
    EducationCreate,
    ExperienceCreate,
    PreferenceInput,
    ProjectCreate,
    SkillCreate,
)
from backend.app.services.audit import record_event


class CandidateConflictError(ValueError):
    pass


def owned_candidate(db: Session, user: User, candidate_id: str) -> CandidateProfile | None:
    return db.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id, CandidateProfile.owner_id == user.id)
    ).scalar_one_or_none()


def list_candidates(db: Session, user: User, include_archived: bool = False) -> list[CandidateProfile]:
    statement = select(CandidateProfile).where(CandidateProfile.owner_id == user.id)
    if not include_archived:
        statement = statement.where(CandidateProfile.is_archived.is_(False))
    return list(db.execute(statement.order_by(CandidateProfile.created_at)).scalars())


def create_candidate(db: Session, user: User, payload: CandidateCreate) -> CandidateProfile:
    candidate = CandidateProfile(owner_id=user.id, **payload.model_dump())
    db.add(candidate)
    try:
        db.flush()
        record_event(
            db,
            owner_id=user.id,
            candidate_id=candidate.id,
            action="candidate.created",
            entity_type="candidate_profile",
            entity_id=candidate.id,
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CandidateConflictError("A candidate with this display name already exists") from error
    db.refresh(candidate)
    return candidate


def update_candidate(db: Session, candidate: CandidateProfile, payload: CandidateUpdate) -> CandidateProfile:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CandidateConflictError("A candidate with this display name already exists") from error
    db.refresh(candidate)
    return candidate


def upsert_preference(db: Session, candidate: CandidateProfile, payload: PreferenceInput) -> CandidatePreference:
    preference = candidate.preference
    if preference is None:
        preference = CandidatePreference(candidate_id=candidate.id)
        db.add(preference)
    for key, value in payload.model_dump().items():
        setattr(preference, key, value)
    db.commit()
    db.refresh(preference)
    return preference


def add_skill(db: Session, candidate: CandidateProfile, payload: SkillCreate) -> CandidateSkill:
    name = payload.name.strip()
    skill = CandidateSkill(
        candidate_id=candidate.id,
        name=name,
        normalized_name=" ".join(name.casefold().split()),
        years_experience=payload.years_experience,
        confirmed=True,
        source="user",
    )
    db.add(skill)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CandidateConflictError("This skill already exists") from error
    db.refresh(skill)
    return skill


def add_experience(db: Session, candidate: CandidateProfile, payload: ExperienceCreate) -> EmploymentExperience:
    experience = EmploymentExperience(candidate_id=candidate.id, **payload.model_dump(), confirmed=True, source="user")
    db.add(experience)
    db.commit()
    db.refresh(experience)
    return experience


def add_project(db: Session, candidate: CandidateProfile, payload: ProjectCreate) -> ProjectExperience:
    project = ProjectExperience(candidate_id=candidate.id, **payload.model_dump(), confirmed=True, source="user")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def add_education(db: Session, candidate: CandidateProfile, payload: EducationCreate) -> Education:
    education = Education(candidate_id=candidate.id, **payload.model_dump(), confirmed=True, source="user")
    db.add(education)
    db.commit()
    db.refresh(education)
    return education


def add_certification(db: Session, candidate: CandidateProfile, payload: CertificationCreate) -> Certification:
    certification = Certification(candidate_id=candidate.id, **payload.model_dump(), confirmed=True, source="user")
    db.add(certification)
    db.commit()
    db.refresh(certification)
    return certification


def upsert_answer(db: Session, candidate: CandidateProfile, payload: AnswerCreate) -> ApplicationAnswer:
    answer = db.execute(
        select(ApplicationAnswer).where(
            ApplicationAnswer.candidate_id == candidate.id,
            ApplicationAnswer.question_key == payload.question_key,
        )
    ).scalar_one_or_none()
    if answer is None:
        answer = ApplicationAnswer(candidate_id=candidate.id, question_key=payload.question_key)
        db.add(answer)
    answer.answer = payload.answer
    answer.sensitive = payload.sensitive
    answer.require_confirmation_each_time = payload.require_confirmation_each_time or payload.sensitive
    db.commit()
    db.refresh(answer)
    return answer


def list_skills(db: Session, candidate: CandidateProfile) -> list[CandidateSkill]:
    return list(db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)).scalars())


def list_experiences(db: Session, candidate: CandidateProfile) -> list[EmploymentExperience]:
    return list(
        db.execute(
            select(EmploymentExperience)
            .where(EmploymentExperience.candidate_id == candidate.id)
            .order_by(EmploymentExperience.start_date.desc())
        ).scalars()
    )


def list_projects(db: Session, candidate: CandidateProfile) -> list[ProjectExperience]:
    return list(db.execute(select(ProjectExperience).where(ProjectExperience.candidate_id == candidate.id)).scalars())


def list_education(db: Session, candidate: CandidateProfile) -> list[Education]:
    return list(db.execute(select(Education).where(Education.candidate_id == candidate.id)).scalars())


def list_certifications(db: Session, candidate: CandidateProfile) -> list[Certification]:
    return list(db.execute(select(Certification).where(Certification.candidate_id == candidate.id)).scalars())


def list_answers(db: Session, candidate: CandidateProfile) -> list[ApplicationAnswer]:
    return list(db.execute(select(ApplicationAnswer).where(ApplicationAnswer.candidate_id == candidate.id)).scalars())


def list_resumes(db: Session, candidate: CandidateProfile) -> list[Resume]:
    return list(
        db.execute(
            select(Resume).where(Resume.candidate_id == candidate.id).order_by(Resume.created_at.desc())
        ).scalars()
    )
