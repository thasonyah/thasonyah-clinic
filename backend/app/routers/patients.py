import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.identity import UserOutput
from app.schemas.records import (
    ConsentAttachmentOutput,
    PatientInput,
    PatientOutput,
    PatientUpdate,
    VisitInput,
    VisitOutput,
)
from app.services import records

router = APIRouter(prefix="/patients", tags=["patients"])
read = require_roles("reception", "practitioner")
clinical = require_roles("practitioner")


@router.get("/providers", response_model=list[UserOutput])
def providers(user=Depends(require_roles("reception")), db: Session = Depends(get_session)):
    return records.list_providers(db)


@router.get("", response_model=list[PatientOutput])
def patients(
    q: str = Query("", max_length=100),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(read),
    db: Session = Depends(get_session),
):
    return records.list_patients(db, user, q, limit, offset)


@router.post("", response_model=PatientOutput, status_code=201)
def create(
    payload: PatientInput,
    user=Depends(require_roles("reception")),
    db: Session = Depends(get_session),
):
    return records.create_patient(db, user, payload)


@router.get("/{patient_id}", response_model=PatientOutput)
def detail(patient_id: uuid.UUID, user=Depends(read), db: Session = Depends(get_session)):
    return records.get_patient(db, user, patient_id)


@router.get("/{patient_id}/visits", response_model=list[VisitOutput])
def visits(patient_id: uuid.UUID, user=Depends(clinical), db: Session = Depends(get_session)):
    return records.list_visits(db, user, patient_id)


@router.post("/{patient_id}/visits", response_model=VisitOutput, status_code=201)
def new_visit(
    patient_id: uuid.UUID,
    payload: VisitInput,
    user=Depends(clinical),
    db: Session = Depends(get_session),
):
    return records.create_visit(db, user, patient_id, payload)


@router.patch("/{patient_id}", response_model=PatientOutput)
def correct(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    user=Depends(require_roles("reception")),
    db: Session = Depends(get_session),
):
    return records.correct_patient(db, user, patient_id, payload)


@router.post("/{patient_id}/print-log", status_code=204)
def print_log(patient_id: uuid.UUID, user=Depends(clinical), db: Session = Depends(get_session)):
    records.record_export(db, user, patient_id)


@router.get("/{patient_id}/consents", response_model=list[ConsentAttachmentOutput])
def consents(patient_id: uuid.UUID, user=Depends(read), db: Session = Depends(get_session)):
    return records.list_consents(db, user, patient_id)


@router.post("/{patient_id}/consents", response_model=ConsentAttachmentOutput, status_code=201)
async def upload_consent(
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    visit_id: uuid.UUID | None = Form(default=None),
    note: str = Form(default="", max_length=1000),
    user=Depends(read),
    db: Session = Depends(get_session),
):
    return records.store_consent(
        db,
        user,
        patient_id,
        visit_id,
        file.filename or "consent",
        file.content_type or "application/octet-stream",
        note,
        await file.read(records.MAX_CONSENT_BYTES + 1),
    )


@router.get("/{patient_id}/consents/{consent_id}")
def download_consent(
    patient_id: uuid.UUID,
    consent_id: uuid.UUID,
    user=Depends(read),
    db: Session = Depends(get_session),
):
    consent = records.get_consent(db, user, patient_id, consent_id)
    return Response(
        consent.data,
        media_type=consent.content_type,
        headers={"Content-Disposition": f'attachment; filename="{consent.filename}"'},
    )
