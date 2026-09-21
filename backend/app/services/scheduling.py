from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from app.models.identity import User
from app.models.records import Patient
from app.models.scheduling import Appointment, Resource
from app.schemas.scheduling import AppointmentOutput
from app.services.audit import record


def list_resources(db):
    return list(db.scalars(select(Resource).order_by(Resource.name)))


def create_resource(db, user, payload):
    resource = Resource(**payload.model_dump())
    db.add(resource)
    try:
        db.flush()
        record(db, user, "resource.create", resource.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Resource name already exists") from None
    return resource


def output(db, appointment):
    result = AppointmentOutput.model_validate(appointment)
    result.patient_name = db.get(Patient, appointment.patient_id).name
    return result


def list_appointments(db, user, day):
    zone = ZoneInfo("Asia/Bangkok")
    day = day or datetime.now(zone).date()
    start = datetime.combine(day, time.min, tzinfo=zone)
    statement = select(Appointment).where(
        Appointment.starts_at < start + timedelta(days=1), Appointment.ends_at > start
    )
    if user.role == "practitioner":
        statement = statement.where(Appointment.provider_id == user.id)
    return [output(db, a) for a in db.scalars(statement.order_by(Appointment.starts_at).limit(500))]


def create_appointment(db, user, payload):
    # Every writer takes locks in this order. This serialises competing slots across workers.
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id).with_for_update())
    if not patient:
        raise HTTPException(404, "Patient not found")
    provider = db.scalar(select(User).where(User.id == patient.provider_id).with_for_update())
    if not provider.active or provider.role != "practitioner":
        raise HTTPException(409, "Practitioner inactive")
    old = db.scalar(select(Appointment).where(Appointment.request_id == payload.request_id))
    if old:
        if old.created_by != user.id or any(
            getattr(old, k) != v for k, v in payload.model_dump().items()
        ):
            raise HTTPException(409, "Request key reused for different booking")
        return output(db, old)
    resources = [Appointment.provider_id == provider.id, Appointment.patient_id == patient.id]
    if payload.resource_id:
        resource = db.scalar(
            select(Resource).where(Resource.id == payload.resource_id).with_for_update()
        )
        if not resource or not resource.active:
            raise HTTPException(422, "Resource unavailable")
        resources.append(Appointment.resource_id == resource.id)
    conflict = db.scalar(
        select(Appointment.id)
        .where(
            or_(*resources),
            Appointment.status != "cancelled",
            Appointment.starts_at < payload.ends_at,
            Appointment.ends_at > payload.starts_at,
        )
        .limit(1)
    )
    if conflict:
        raise HTTPException(409, "Practitioner, patient or resource already booked")
    appointment = Appointment(**payload.model_dump(), provider_id=provider.id, created_by=user.id)
    db.add(appointment)
    try:
        db.flush()
        record(db, user, "appointment.create", appointment.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Booking request already exists") from None
    return output(db, appointment)


def change_status(db, user, appointment_id, payload):
    appointment = db.get(Appointment, appointment_id)
    if not appointment or (user.role == "practitioner" and appointment.provider_id != user.id):
        raise HTTPException(404, "Appointment not found")
    transitions = {
        "reception": {"booked": {"arrived", "cancelled"}, "arrived": {"cancelled"}},
        "practitioner": {"arrived": {"in_service"}, "in_service": {"completed"}},
    }
    if payload.status not in transitions[user.role].get(appointment.status, set()):
        raise HTTPException(409, "Invalid queue transition")
    changed = db.execute(
        update(Appointment)
        .where(
            Appointment.id == appointment_id,
            Appointment.version == payload.expected_version,
            Appointment.status == appointment.status,
        )
        .values(status=payload.status, version=Appointment.version + 1)
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Appointment changed; reload")
    record(db, user, "appointment." + payload.status, appointment_id)
    db.commit()
    return output(db, db.get(Appointment, appointment_id))


def reschedule(db, user, appointment_id, payload):
    original = db.get(Appointment, appointment_id)
    if not original:
        raise HTTPException(404, "Appointment not found")
    db.scalar(select(Patient).where(Patient.id == original.patient_id).with_for_update())
    provider = db.scalar(select(User).where(User.id == original.provider_id).with_for_update())
    if not provider.active:
        raise HTTPException(409, "Practitioner inactive")
    resource_filters = [
        Appointment.provider_id == provider.id,
        Appointment.patient_id == original.patient_id,
    ]
    if payload.resource_id:
        resource = db.scalar(
            select(Resource).where(Resource.id == payload.resource_id).with_for_update()
        )
        if not resource or not resource.active:
            raise HTTPException(422, "Resource unavailable")
        resource_filters.append(Appointment.resource_id == resource.id)
    conflict = db.scalar(
        select(Appointment.id)
        .where(
            Appointment.id != appointment_id,
            Appointment.status != "cancelled",
            or_(*resource_filters),
            Appointment.starts_at < payload.ends_at,
            Appointment.ends_at > payload.starts_at,
        )
        .limit(1)
    )
    if conflict:
        raise HTTPException(409, "New slot unavailable; original booking unchanged")
    changed = db.execute(
        update(Appointment)
        .where(
            Appointment.id == appointment_id,
            Appointment.version == payload.expected_version,
            Appointment.status == "booked",
        )
        .values(**payload.model_dump(exclude={"expected_version"}), version=Appointment.version + 1)
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Booking changed or already checked in")
    record(db, user, "appointment.reschedule", appointment_id)
    db.commit()
    return output(db, db.get(Appointment, appointment_id))


def resource_status(db, user, resource_id, active):
    resource = db.scalar(select(Resource).where(Resource.id == resource_id).with_for_update())
    if not resource:
        raise HTTPException(404, "Resource not found")
    resource.active = active
    record(db, user, "resource.status", resource_id)
    db.commit()
    return resource
