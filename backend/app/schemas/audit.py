from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str | None
    action: str
    entity_type: str
    entity_id: str | None
    metadata_json: dict
    created_at: datetime
