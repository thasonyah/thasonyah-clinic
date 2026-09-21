import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.records import (
    AmendmentInput,
    AmendmentOutput,
    VersionInput,
    VisitOutput,
    VisitUpdate,
)
from app.services import records

router = APIRouter(prefix="/visits", tags=["visits"])
clinical = require_roles("practitioner")


@router.patch("/{visit_id}", response_model=VisitOutput)
def update(
    visit_id: uuid.UUID,
    payload: VisitUpdate,
    user=Depends(clinical),
    db: Session = Depends(get_session),
):
    return records.update_visit(db, user, visit_id, payload)


@router.post("/{visit_id}/sign", response_model=VisitOutput)
def sign(
    visit_id: uuid.UUID,
    payload: VersionInput,
    user=Depends(clinical),
    db: Session = Depends(get_session),
):
    return records.update_visit(db, user, visit_id, payload, sign=True)


@router.get("/{visit_id}/amendments", response_model=list[AmendmentOutput])
def amendments(visit_id: uuid.UUID, user=Depends(clinical), db: Session = Depends(get_session)):
    return records.list_amendments(db, user, visit_id)


@router.post("/{visit_id}/amendments", response_model=AmendmentOutput, status_code=201)
def amend(
    visit_id: uuid.UUID,
    payload: AmendmentInput,
    user=Depends(clinical),
    db: Session = Depends(get_session),
):
    return records.amend_visit(db, user, visit_id, payload)
