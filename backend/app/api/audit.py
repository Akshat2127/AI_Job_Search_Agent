from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.identity import User
from backend.app.schemas.audit import AuditEventOut
from backend.app.security.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
def list_audit_events(
    candidate_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    statement = select(AuditEvent).where(AuditEvent.owner_id == user.id)
    if candidate_id is not None:
        statement = statement.where(AuditEvent.candidate_id == candidate_id)
    return list(db.execute(statement.order_by(AuditEvent.created_at.desc()).limit(limit)).scalars())
