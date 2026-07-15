from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
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
    AnswerOut,
    CandidateCreate,
    CandidateOut,
    CandidateUpdate,
    CertificationCreate,
    CertificationOut,
    EducationCreate,
    EducationOut,
    ExperienceCreate,
    ExperienceOut,
    PreferenceInput,
    PreferenceOut,
    ProjectCreate,
    ProjectOut,
    ResumeOut,
    ResumeReviewUpdate,
    SkillCreate,
    SkillOut,
)
from backend.app.security.auth import get_current_user
from backend.app.services import candidates as service
from backend.app.services.audit import record_event
from backend.app.services.resumes import ResumeDuplicateError, ResumeValidationError, delete_resume_file, store_resume

router = APIRouter(prefix="/candidates", tags=["candidates"])


def require_candidate(candidate_id: str, user: User, db: Session) -> CandidateProfile:
    candidate = service.owned_candidate(db, user, candidate_id)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")
    return candidate


@router.get("", response_model=list[CandidateOut])
def candidates(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CandidateProfile]:
    return service.list_candidates(db, user, include_archived)


@router.post("", response_model=CandidateOut, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfile:
    try:
        return service.create_candidate(db, user, payload)
    except service.CandidateConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfile:
    return require_candidate(candidate_id, user, db)


@router.patch("/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfile:
    try:
        return service.update_candidate(db, require_candidate(candidate_id, user, db), payload)
    except service.CandidateConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.put("/{candidate_id}/preferences", response_model=PreferenceOut)
def put_preferences(
    candidate_id: str,
    payload: PreferenceInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidatePreference:
    return service.upsert_preference(db, require_candidate(candidate_id, user, db), payload)


@router.post("/{candidate_id}/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(
    candidate_id: str,
    payload: SkillCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateSkill:
    try:
        return service.add_skill(db, require_candidate(candidate_id, user, db), payload)
    except service.CandidateConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.get("/{candidate_id}/skills", response_model=list[SkillOut])
def skills(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CandidateSkill]:
    return service.list_skills(db, require_candidate(candidate_id, user, db))


@router.post("/{candidate_id}/experiences", response_model=ExperienceOut, status_code=status.HTTP_201_CREATED)
def create_experience(
    candidate_id: str,
    payload: ExperienceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmploymentExperience:
    return service.add_experience(db, require_candidate(candidate_id, user, db), payload)


@router.get("/{candidate_id}/experiences", response_model=list[ExperienceOut])
def experiences(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[EmploymentExperience]:
    return service.list_experiences(db, require_candidate(candidate_id, user, db))


@router.post("/{candidate_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    candidate_id: str,
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectExperience:
    return service.add_project(db, require_candidate(candidate_id, user, db), payload)


@router.get("/{candidate_id}/projects", response_model=list[ProjectOut])
def projects(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ProjectExperience]:
    return service.list_projects(db, require_candidate(candidate_id, user, db))


@router.post("/{candidate_id}/education", response_model=EducationOut, status_code=status.HTTP_201_CREATED)
def create_education(
    candidate_id: str,
    payload: EducationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Education:
    return service.add_education(db, require_candidate(candidate_id, user, db), payload)


@router.get("/{candidate_id}/education", response_model=list[EducationOut])
def education(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Education]:
    return service.list_education(db, require_candidate(candidate_id, user, db))


@router.post("/{candidate_id}/certifications", response_model=CertificationOut, status_code=status.HTTP_201_CREATED)
def create_certification(
    candidate_id: str,
    payload: CertificationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Certification:
    return service.add_certification(db, require_candidate(candidate_id, user, db), payload)


@router.get("/{candidate_id}/certifications", response_model=list[CertificationOut])
def certifications(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Certification]:
    return service.list_certifications(db, require_candidate(candidate_id, user, db))


@router.put("/{candidate_id}/answers", response_model=AnswerOut)
def put_answer(
    candidate_id: str,
    payload: AnswerCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationAnswer:
    return service.upsert_answer(db, require_candidate(candidate_id, user, db), payload)


@router.get("/{candidate_id}/answers", response_model=list[AnswerOut])
def answers(
    candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ApplicationAnswer]:
    return service.list_answers(db, require_candidate(candidate_id, user, db))


@router.post("/{candidate_id}/resumes", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    candidate_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    try:
        return await store_resume(db, require_candidate(candidate_id, user, db), file)
    except ResumeDuplicateError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except ResumeValidationError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


@router.get("/{candidate_id}/resumes", response_model=list[ResumeOut])
def resumes(candidate_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Resume]:
    return service.list_resumes(db, require_candidate(candidate_id, user, db))


@router.patch("/{candidate_id}/resumes/{resume_id}", response_model=ResumeOut)
def review_resume(
    candidate_id: str,
    resume_id: str,
    payload: ResumeReviewUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    candidate = require_candidate(candidate_id, user, db)
    resume = next((item for item in service.list_resumes(db, candidate) if item.id == resume_id), None)
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")
    resume.review_status = payload.review_status
    if payload.extracted_text is not None:
        resume.extracted_text = payload.extracted_text
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate.id,
        action="resume.reviewed",
        entity_type="resume",
        entity_id=resume.id,
        metadata={"review_status": payload.review_status},
    )
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{candidate_id}/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    candidate_id: str,
    resume_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    candidate = require_candidate(candidate_id, user, db)
    resume = next((item for item in service.list_resumes(db, candidate) if item.id == resume_id), None)
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")
    delete_resume_file(resume)
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate.id,
        action="resume.deleted",
        entity_type="resume",
        entity_id=resume.id,
    )
    db.delete(resume)
    db.commit()
