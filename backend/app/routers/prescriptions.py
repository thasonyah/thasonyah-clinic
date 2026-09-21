import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.pharmacy import DispenseInput, PrescriptionInput, PrescriptionOutput
from app.services import pharmacy

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.get("", response_model=list[PrescriptionOutput])
def listing(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(require_roles("practitioner", "pharmacy")),
    db: Session = Depends(get_session),
):
    return pharmacy.prescriptions(db, user, limit, offset)


@router.post("", response_model=PrescriptionOutput, status_code=201)
def prescribe(
    payload: PrescriptionInput,
    user=Depends(require_roles("practitioner")),
    db: Session = Depends(get_session),
):
    return pharmacy.prescribe(db, user, payload)


@router.post("/{prescription_id}/dispense", response_model=PrescriptionOutput)
def dispense(
    prescription_id: uuid.UUID,
    payload: DispenseInput,
    user=Depends(require_roles("pharmacy")),
    db: Session = Depends(get_session),
):
    return pharmacy.dispense(db, user, prescription_id, payload)


@router.post("/{prescription_id}/cancel", response_model=PrescriptionOutput)
def cancel(
    prescription_id: uuid.UUID,
    user=Depends(require_roles("practitioner")),
    db: Session = Depends(get_session),
):
    return pharmacy.cancel(db, user, prescription_id)
