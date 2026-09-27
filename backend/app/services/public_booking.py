from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.catalog import ClinicService
from app.models.scheduling import BookingRequest

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
