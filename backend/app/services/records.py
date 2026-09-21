import hashlib
from datetime import datetime, timezone
from pathlib import PurePath

from fastapi import HTTPException
from sqlalchemy import String, cast, or_, select, update

from app.models.identity import User
from app.models.records import ConsentAttachment, Patient, Visit, VisitAmendment
from app.services import zodiac
from app.services.audit import record

MAX_CONSENT_BYTES = 5 * 1024 * 1024
CONSENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def patient_scope(query, user):
    if user.role == "practitioner":
        query = query.where(Patient.provider_id == user.id)
    return query


def list_patients(db, user, query, limit, offset):
    statement = patient_scope(select(Patient), user)
    if query:
        statement = statement.where(
            or_(
                Patient.name.contains(query, autoescape=True),
                Patient.phone.contains(query, autoescape=True),
                cast(Patient.id, String).contains(query, autoescape=True),
            )
        )
    rows = list(db.scalars(statement.order_by(Patient.id).limit(limit).offset(offset)))
    record(db, user, "patient.search", "registry")
    db.commit()
    return rows


def get_patient(db, user, patient_id):
    patient = db.scalar(patient_scope(select(Patient).where(Patient.id == patient_id), user))
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


def create_patient(db, user, payload):
    provider = db.get(User, payload.provider_id)
    if not provider or not provider.active or provider.role != "practitioner":
        raise HTTPException(422, "Choose an active practitioner")
    values = zodiac.fill_lunar_inputs(payload.model_dump())
    patient = Patient(**values, created_by=user.id)
    db.add(patient)
    db.flush()
    record(db, user, "patient.create", patient.id)
    db.commit()
    return patient


def list_providers(db):
    return list(
        db.scalars(
            select(User)
            .where(User.role == "practitioner", User.active.is_(True))
            .order_by(User.email)
            .limit(100)
        )
    )


def list_visits(db, user, patient_id):
    get_patient(db, user, patient_id)
    return list(
        db.scalars(
            select(Visit)
            .where(Visit.patient_id == patient_id, Visit.provider_id == user.id)
            .order_by(Visit.created_at.desc())
            .limit(100)
        )
    )


def create_visit(db, user, patient_id, payload):
    get_patient(db, user, patient_id)
    visit = Visit(
        **payload.model_dump(),
        patient_id=patient_id,
        provider_id=user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(visit)
    db.flush()
    record(db, user, "visit.create", visit.id)
    db.commit()
    return visit


def update_visit(db, user, visit_id, payload, sign=False):
    owned = db.scalar(
        select(Visit.id)
        .join(Patient)
        .where(Visit.id == visit_id, Visit.provider_id == user.id, Patient.provider_id == user.id)
    )
    if not owned:
        raise HTTPException(404, "Visit not found")
    values = (
        {"signed_at": datetime.now(timezone.utc)}
        if sign
        else payload.model_dump(exclude={"expected_version"})
    )
    changed = db.execute(
        update(Visit)
        .where(
            Visit.id == visit_id,
            Visit.provider_id == user.id,
            Visit.version == payload.expected_version,
            Visit.signed_at.is_(None),
        )
        .values(**values, version=Visit.version + 1)
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Visit changed or already signed")
    record(db, user, "visit.sign" if sign else "visit.update", visit_id)
    db.commit()
    return db.get(Visit, visit_id)


def owned_visit(db, user, visit_id):
    visit = db.scalar(
        select(Visit)
        .join(Patient)
        .where(Visit.id == visit_id, Visit.provider_id == user.id, Patient.provider_id == user.id)
    )
    if not visit:
        raise HTTPException(404, "Visit not found")
    return visit


def list_amendments(db, user, visit_id):
    owned_visit(db, user, visit_id)
    return list(
        db.scalars(
            select(VisitAmendment)
            .where(VisitAmendment.visit_id == visit_id)
            .order_by(VisitAmendment.created_at)
        )
    )


def amend_visit(db, user, visit_id, payload):
    visit = owned_visit(db, user, visit_id)
    if not visit.signed_at:
        raise HTTPException(409, "Sign the original before adding an amendment")
    amendment = VisitAmendment(
        **payload.model_dump(),
        visit_id=visit.id,
        author_id=user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(amendment)
    db.flush()
    record(db, user, "visit.amend", amendment.id)
    db.commit()
    return amendment


def correct_patient(db, user, patient_id, payload):
    patient = get_patient(db, user, patient_id)
    if patient.provider_id != payload.provider_id:
        raise HTTPException(422, "Provider transfer requires a separate clinical handover")
    changed = db.execute(
        update(Patient)
        .where(Patient.id == patient_id, Patient.version == payload.expected_version)
        .values(
            **zodiac.fill_lunar_inputs(payload.model_dump(exclude={"expected_version"})),
            version=Patient.version + 1,
        )
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Patient changed; reload before editing")
    record(db, user, "patient.update", patient_id)
    db.commit()
    return db.get(Patient, patient_id)


def record_export(db, user, patient_id):
    get_patient(db, user, patient_id)
    record(db, user, "patient.print_requested", patient_id)
    db.commit()


def list_consents(db, user, patient_id):
    get_patient(db, user, patient_id)
    return list(
        db.scalars(
            select(ConsentAttachment)
            .where(ConsentAttachment.patient_id == patient_id)
            .order_by(ConsentAttachment.created_at.desc())
            .limit(100)
        )
    )


def store_consent(db, user, patient_id, visit_id, filename, content_type, note, data):
    get_patient(db, user, patient_id)
    if visit_id:
        visit = db.get(Visit, visit_id)
        if not visit or visit.patient_id != patient_id:
            raise HTTPException(422, "Visit does not belong to this patient")
        if user.role == "practitioner" and visit.provider_id != user.id:
            raise HTTPException(404, "Visit not found")
    if content_type not in CONSENT_TYPES:
        raise HTTPException(422, "Use PDF, JPEG, or PNG consent files")
    if not data or len(data) > MAX_CONSENT_BYTES:
        raise HTTPException(422, "Consent file must be 1 byte to 5 MB")
    safe_name = PurePath(filename or "consent").name[:240] or "consent"
    safe_name = "".join(
        ch if ch.isprintable() and ch not in {'"', "\\"} else "_" for ch in safe_name
    )
    consent = ConsentAttachment(
        patient_id=patient_id,
        visit_id=visit_id,
        filename=safe_name,
        content_type=content_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        note=note,
        data=data,
        uploaded_by=user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(consent)
    db.flush()
    record(db, user, "patient.consent_upload", consent.id)
    db.commit()
    return consent


def get_consent(db, user, patient_id, consent_id):
    get_patient(db, user, patient_id)
    consent = db.scalar(
        select(ConsentAttachment).where(
            ConsentAttachment.id == consent_id, ConsentAttachment.patient_id == patient_id
        )
    )
    if not consent:
        raise HTTPException(404, "Consent attachment not found")
    record(db, user, "patient.consent_download", consent.id)
    db.commit()
    return consent
