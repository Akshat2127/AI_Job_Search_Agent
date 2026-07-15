from sqlalchemy.orm import Session

from backend.app.models.audit import AuditEvent


def record_event(
    db: Session,
    *,
    owner_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    candidate_id: str | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        owner_id=owner_id,
        candidate_id=candidate_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
