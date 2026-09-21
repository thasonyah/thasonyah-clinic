import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.scheduling import (
    AppointmentInput,
    AppointmentMove,
    AppointmentOutput,
    AppointmentStatus,
)
from app.services import scheduling

router = APIRouter(prefix="/appointments", tags=["appointments"])
access = require_roles("reception", "practitioner")


@router.get("", response_model=list[AppointmentOutput])
def listing(day: date | None = None, user=Depends(access), db: Session = Depends(get_session)):
    return scheduling.list_appointments(db, user, day)


@router.post("", response_model=AppointmentOutput, status_code=201)
def create(
    payload: AppointmentInput,
    user=Depends(require_roles("reception")),
    db: Session = Depends(get_session),
):
    return scheduling.create_appointment(db, user, payload)


@router.patch("/{appointment_id}/status", response_model=AppointmentOutput)
def status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatus,
    user=Depends(access),
    db: Session = Depends(get_session),
):
    return scheduling.change_status(db, user, appointment_id, payload)


@router.patch("/{appointment_id}", response_model=AppointmentOutput)
def move(
    appointment_id: uuid.UUID,
    payload: AppointmentMove,
    user=Depends(require_roles("reception")),
    db: Session = Depends(get_session),
):
    return scheduling.reschedule(db, user, appointment_id, payload)
