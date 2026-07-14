import hashlib
import io
import zipfile
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.candidate import CandidateProfile, Resume
from backend.app.models.identity import uuid_string

PDF_TYPE = "application/pdf"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_TYPES = {PDF_TYPE: ".pdf", DOCX_TYPE: ".docx"}


class ResumeValidationError(ValueError):
    pass


def _validate_signature(content: bytes, media_type: str) -> None:
    if media_type == PDF_TYPE and not content.startswith(b"%PDF-"):
        raise ResumeValidationError("File content is not a valid PDF")
    if media_type == DOCX_TYPE:
        if not content.startswith(b"PK"):
            raise ResumeValidationError("File content is not a valid DOCX")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ResumeValidationError("File content is not a valid DOCX")
        except zipfile.BadZipFile as error:
            raise ResumeValidationError("File content is not a valid DOCX") from error


def extract_text(content: bytes, media_type: str) -> str:
    try:
        if media_type == PDF_TYPE:
            return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages).strip()
        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception as error:
        raise ResumeValidationError("The resume could not be parsed") from error


async def store_resume(db: Session, candidate: CandidateProfile, upload: UploadFile) -> Resume:
    media_type = upload.content_type or ""
    expected_suffix = ALLOWED_TYPES.get(media_type)
    if expected_suffix is None:
        raise ResumeValidationError("Only PDF and DOCX resumes are supported")
    original_name = Path(upload.filename or "resume").name
    if Path(original_name).suffix.casefold() != expected_suffix:
        raise ResumeValidationError("Filename extension does not match the uploaded file type")
    content = await upload.read(settings.max_resume_bytes + 1)
    if not content:
        raise ResumeValidationError("Resume file is empty")
    if len(content) > settings.max_resume_bytes:
        raise ResumeValidationError(f"Resume exceeds the {settings.max_resume_bytes}-byte limit")
    _validate_signature(content, media_type)
    text = extract_text(content, media_type)

    storage_root = Path(settings.upload_root).resolve()
    candidate_dir = (storage_root / candidate.owner_id / candidate.id).resolve()
    if storage_root not in candidate_dir.parents:
        raise ResumeValidationError("Invalid resume storage path")
    candidate_dir.mkdir(parents=True, exist_ok=True)
    storage_path = candidate_dir / f"{uuid_string()}{expected_suffix}"
    storage_path.write_bytes(content)

    resume = Resume(
        candidate_id=candidate.id,
        original_filename=original_name,
        storage_key=str(storage_path.relative_to(storage_root)),
        media_type=media_type,
        byte_size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        extracted_text=text,
        review_status="needs_review",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume
