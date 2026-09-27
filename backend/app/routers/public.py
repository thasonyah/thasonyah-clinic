import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import public_access, require_roles
from app.schemas.public import (
    BookingRequestConfirm,
    BookingRequestConfirmOutput,
    BookingRequestInput,
    BookingRequestOutput,
    BookingRequestStatus,
    PublicServiceOutput,
)
from app.services import public_booking

public_router = APIRouter(prefix="/public", tags=["public"])
booking_router = APIRouter(prefix="/booking-requests", tags=["booking-requests"])
limiter = Limiter(key_func=get_remote_address)


@public_router.get(
    "/services", response_model=list[PublicServiceOutput], dependencies=[Depends(public_access)]
)
def public_services(db: Session = Depends(get_session)):
    return public_booking.list_public_services(db)


@public_router.post(
    "/bookings",
    response_model=BookingRequestOutput,
    status_code=201,
    dependencies=[Depends(public_access)],
)
@limiter.limit("6/minute")
def create_booking(
    request: Request, payload: BookingRequestInput, db: Session = Depends(get_session)
):
    return public_booking.create_booking_request(db, payload)


@booking_router.get("", response_model=list[BookingRequestOutput])
def list_requests(
    day: date | None = None,
    user=Depends(require_roles("reception", "practitioner", "manager", "admin")),
    db: Session = Depends(get_session),
):
    return public_booking.list_booking_requests(db, day)


@booking_router.patch("/{booking_id}/status", response_model=BookingRequestOutput)
def update_request_status(
    booking_id: uuid.UUID,
    payload: BookingRequestStatus,
    user=Depends(require_roles("reception", "manager", "admin")),
    db: Session = Depends(get_session),
):
    return public_booking.change_booking_status(db, booking_id, payload)


@booking_router.post("/{booking_id}/confirm", response_model=BookingRequestConfirmOutput)
def confirm_request(
    booking_id: uuid.UUID,
    payload: BookingRequestConfirm,
    user=Depends(require_roles("reception", "manager", "admin")),
    db: Session = Depends(get_session),
):
    return public_booking.confirm_booking_request(db, user, booking_id, payload)
