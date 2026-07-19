import hashlib
import json
import re
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.models.identity import User
from backend.app.models.ingestion import IngestionRun, JobSourceRecord
from backend.app.models.job import Job
from backend.app.schemas.job import JobCreate
from backend.app.services.ats_connectors import ConnectorError, ExternalJob, JobConnector, connector_for
from backend.app.services.audit import record_event

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {"gh_jid", "lever-source", "source", "ref", "referrer"}
MANUAL_TRACKING_QUERY_KEYS = TRACKING_QUERY_KEYS | {
    "currentjobid",
    "from",
    "original_referer",
    "position",
    "referenceid",
    "trackingid",
}
MAX_RAW_PAYLOAD_BYTES = 256_000


class ConnectorExecutionFailed(RuntimeError):
    def __init__(self, run: IngestionRun, status_code: int) -> None:
        super().__init__(run.error_message or "Connector execution failed")
        self.run = run
        self.status_code = status_code


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def plain_text(value: str | None) -> str | None:
    if value is None:
        return None
    for _ in range(2):
        decoded = unescape(value)
        if decoded == value:
            break
        value = decoded
    parser = _TextExtractor()
    parser.feed(value)
    text = " ".join(parser.parts)
    return re.sub(r"\s+", " ", text).strip() or None


def canonicalize_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    scheme = parsed.scheme.casefold()
    hostname = (parsed.hostname or "").casefold()
    port = parsed.port
    netloc = hostname if port is None or (scheme, port) in {("http", 80), ("https", 443)} else f"{hostname}:{port}"
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if key.casefold() not in TRACKING_QUERY_KEYS and not key.casefold().startswith(TRACKING_QUERY_PREFIXES)
        )
    )
    return urlunsplit((scheme, netloc, path, query, ""))


def canonicalize_manual_job_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value.strip())
    hostname = (parsed.hostname or "").casefold()
    if hostname == "linkedin.com" or hostname.endswith(".linkedin.com"):
        provider = "linkedin"
        hostname = "www.linkedin.com"
    elif hostname == "indeed.com" or hostname.endswith(".indeed.com"):
        provider = "indeed"
        hostname = "www.indeed.com"
    else:
        raise ValueError("Only LinkedIn and Indeed job URLs are supported")
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if key.casefold() not in MANUAL_TRACKING_QUERY_KEYS
            and not key.casefold().startswith(TRACKING_QUERY_PREFIXES)
        )
    )
    return provider, urlunsplit(("https", hostname, path, query, ""))


def dedupe_key(record: ExternalJob) -> str:
    values = (record.company, record.title, record.location or "")
    normalized = "|".join(" ".join(value.casefold().split()) for value in values)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _payload(record: ExternalJob) -> dict:
    payload = record.raw_payload or {}
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    if len(encoded) > MAX_RAW_PAYLOAD_BYTES:
        raise ValueError("Raw connector payload exceeds the ingestion limit")
    return payload


def ingest_records(
    db: Session,
    user: User,
    candidate: CandidateProfile,
    provider: str,
    source_key: str,
    records: list[ExternalJob],
    run: IngestionRun | None = None,
) -> IngestionRun:
    if run is None:
        run = IngestionRun(
            owner_id=user.id,
            candidate_id=candidate.id,
            provider=provider,
            source_key=source_key,
        )
        db.add(run)
        db.flush()
    run.discovered_count = len(records)
    created = 0
    duplicates = 0

    for record in records:
        validated = JobCreate(
            company=record.company,
            title=record.title,
            location=record.location,
            url=record.url,
            source=provider,
            description=plain_text(record.description),
        )
        canonical_url = canonicalize_url(validated.url)
        fingerprint = dedupe_key(record)
        source_record = db.execute(
            select(JobSourceRecord).where(
                JobSourceRecord.candidate_id == candidate.id,
                JobSourceRecord.provider == provider,
                JobSourceRecord.source_key == source_key,
                JobSourceRecord.external_id == record.external_id,
            )
        ).scalar_one_or_none()
        if source_record is not None:
            source_record.ingestion_run_id = run.id
            source_record.last_seen_at = datetime.now(UTC)
            source_record.raw_payload = _payload(record)
            duplicates += 1
            continue

        job = db.execute(
            select(Job).where(
                Job.candidate_id == candidate.id,
                or_(Job.canonical_url == canonical_url, Job.dedupe_key == fingerprint),
            )
        ).scalar_one_or_none()
        if job is None:
            job = Job(
                **validated.model_dump(),
                owner_id=user.id,
                candidate_id=candidate.id,
                canonical_url=canonical_url,
                dedupe_key=fingerprint,
            )
            db.add(job)
            db.flush()
            created += 1
        else:
            duplicates += 1

        raw_payload = _payload(record)
        db.add(
            JobSourceRecord(
                owner_id=user.id,
                candidate_id=candidate.id,
                job_id=job.id,
                ingestion_run_id=run.id,
                provider=provider,
                source_key=source_key,
                external_id=record.external_id,
                source_url=validated.url,
                canonical_url=canonical_url,
                raw_payload=raw_payload,
                content_hash=hashlib.sha256(json.dumps(raw_payload, sort_keys=True, default=str).encode()).hexdigest(),
            )
        )

    run.created_count = created
    run.duplicate_count = duplicates
    run.status = "completed"
    run.completed_at = datetime.now(UTC)
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate.id,
        action="ingestion.completed",
        entity_type="ingestion_run",
        entity_id=run.id,
        metadata={"provider": provider, "discovered": len(records), "created": created, "duplicates": duplicates},
    )
    db.commit()
    db.refresh(run)
    return run


def execute_connector(
    db: Session,
    user: User,
    candidate: CandidateProfile,
    provider: str,
    source_key: str,
    connector: JobConnector | None = None,
) -> IngestionRun:
    run = IngestionRun(
        owner_id=user.id,
        candidate_id=candidate.id,
        provider=provider,
        source_key=source_key,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        records = (connector or connector_for(provider)).fetch(source_key)
        for record in records:
            if not record.external_id.strip():
                raise ConnectorError("invalid_upstream_response", "The ATS provider returned a job without an ID")
            _payload(record)
        return ingest_records(db, user, candidate, provider, source_key, records, run=run)
    except Exception as error:
        db.rollback()
        persisted = db.get(IngestionRun, run.id)
        if persisted is None:
            raise
        if isinstance(error, ConnectorError):
            code = error.code
            message = str(error)
            status_code = error.status_code
        else:
            code = "ingestion_failed"
            message = "The connector data could not be ingested"
            status_code = 502
        persisted.status = "failed"
        persisted.error_code = code
        persisted.error_message = message
        persisted.completed_at = datetime.now(UTC)
        record_event(
            db,
            owner_id=user.id,
            candidate_id=candidate.id,
            action="ingestion.failed",
            entity_type="ingestion_run",
            entity_id=persisted.id,
            metadata={"provider": provider, "error_code": code},
        )
        db.commit()
        db.refresh(persisted)
        raise ConnectorExecutionFailed(persisted, status_code) from error
