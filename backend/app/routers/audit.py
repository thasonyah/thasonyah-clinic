import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.services.audit import recent

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    target_id: str
    created_at: datetime


@router.get("", response_model=list[AuditOutput])
def events(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_session),
):
    return recent(db, limit, offset)
