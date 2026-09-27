from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from app.models.catalog import ClinicService
from app.models.identity import User
from app.models.records import Patient
from app.models.scheduling import Appointment, BookingRequest, Resource
from app.services.audit import record
from app.services.scheduling import output as appointment_output

BANGKOK = ZoneInfo("Asia/Bangkok")
OPEN_WEEKDAYS = {0, 4, 5, 6}  # Monday, Friday, Saturday, Sunday
OPEN_AT = time(10, 0)
CLOSE_AT = time(22, 0)


def list_public_services(db):
    return list(
        db.scalars(
            select(ClinicService)
            .where(ClinicService.active.is_(True))
            .order_by(ClinicService.name)
            .limit(200)
        )
    )


def _validate_open_hours(starts_at, ends_at):
    start = starts_at.astimezone(BANGKOK)
    end = ends_at.astimezone(BANGKOK)
    if start.date() != end.date():
        raise HTTPException(422, "Booking must start and end on the same clinic day")
    if start < datetime.now(timezone.utc).astimezone(BANGKOK):
        raise HTTPException(422, "Booking must be in the future")
    if start.weekday() not in OPEN_WEEKDAYS:
        raise HTTPException(
            422, "Clinic accepts self booking on Monday, Friday, Saturday and Sunday"
        )
    if start.time() < OPEN_AT or end.time() > CLOSE_AT:
        raise HTTPException(422, "Clinic self booking hours are 10:00-22:00")


def create_booking_request(db, payload):
    _validate_open_hours(payload.preferred_starts_at, payload.preferred_ends_at)
    data = payload.model_dump()
    if payload.service_id:
        service = db.scalar(
            select(ClinicService).where(
                ClinicService.id == payload.service_id, ClinicService.active.is_(True)
            )
        )
        if not service:
            raise HTTPException(422, "Selected service is unavailable")
        data["service_name"] = service.name
        data["preferred_ends_at"] = payload.preferred_starts_at + timedelta(minutes=service.minutes)
    elif not payload.service_name:
        raise HTTPException(422, "Service name is required")
    request = BookingRequest(**data, status="pending", created_at=datetime.now(timezone.utc))
    db.add(request)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(BookingRequest).where(BookingRequest.request_id == payload.request_id)
        )
        if existing:
            return existing
        raise HTTPException(409, "Booking request could not be saved") from None
    return request


def list_booking_requests(db, day=None):
    statement = select(BookingRequest)
    if day:
        start = datetime.combine(day, time.min, tzinfo=BANGKOK)
        end = start + timedelta(days=1)
        statement = statement.where(
            BookingRequest.preferred_starts_at < end,
            BookingRequest.preferred_ends_at > start,
        )
    return list(
        db.scalars(
            statement.order_by(
                BookingRequest.preferred_starts_at.desc(), BookingRequest.created_at.desc()
            ).limit(200)
        )
    )


def change_booking_status(db, request_id, payload):
    request = db.get(BookingRequest, request_id)
    if not request:
        raise HTTPException(404, "Booking request not found")
    changed = db.execute(
        update(BookingRequest)
        .where(BookingRequest.id == request_id, BookingRequest.version == payload.expected_version)
        .values(status=payload.status, version=BookingRequest.version + 1)
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Booking request changed; reload")
    db.commit()
    return db.get(BookingRequest, request_id)


def confirm_booking_request(db, user, request_id, payload):
    request = db.scalar(
        select(BookingRequest).where(BookingRequest.id == request_id).with_for_update()
    )
    if not request:
        raise HTTPException(404, "Booking request not found")
    if request.version != payload.expected_version:
        raise HTTPException(409, "Booking request changed; reload")
    if request.status == "cancelled":
        raise HTTPException(409, "Cancelled request cannot be confirmed")

    provider = db.scalar(select(User).where(User.id == payload.provider_id).with_for_update())
    if not provider or not provider.active or provider.role != "practitioner":
        raise HTTPException(422, "Choose an active practitioner")

    existing_appointment = db.scalar(
        select(Appointment).where(Appointment.request_id == request.request_id).limit(1)
    )
    existing_patient = None
    if existing_appointment:
        existing_patient = db.get(Patient, existing_appointment.patient_id)
        if request.status != "booked":
            request.status = "booked"
            request.version += 1
            record(db, user, "booking_request.confirm", request.id)
            db.commit()
        return {
            "booking_request": request,
            "patient": existing_patient,
            "appointment": appointment_output(db, existing_appointment),
        }

    resource = None
    resource_filters = [Appointment.provider_id == provider.id]
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
            or_(*resource_filters),
            Appointment.status != "cancelled",
            Appointment.starts_at < request.preferred_ends_at,
            Appointment.ends_at > request.preferred_starts_at,
        )
        .limit(1)
    )
    if conflict:
        raise HTTPException(409, "Practitioner or resource already booked")

    patient = Patient(
        name=request.full_name,
        phone=request.phone,
        provider_id=provider.id,
        created_by=user.id,
    )
    db.add(patient)
    db.flush()
    record(db, user, "patient.create", patient.id)

    appointment = Appointment(
        request_id=request.request_id,
        patient_id=patient.id,
        provider_id=provider.id,
        resource_id=resource.id if resource else None,
        starts_at=request.preferred_starts_at,
        ends_at=request.preferred_ends_at,
        created_by=user.id,
    )
    db.add(appointment)
    db.flush()
    request.status = "booked"
    request.version += 1
    record(db, user, "appointment.create", appointment.id)
    record(db, user, "booking_request.confirm", request.id)
    db.commit()
    return {
        "booking_request": request,
        "patient": patient,
        "appointment": appointment_output(db, appointment),
    }
