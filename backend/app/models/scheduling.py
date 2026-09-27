import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (CheckConstraint("ends_at > starts_at"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resources.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="booked")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class BookingRequest(Base):
    __tablename__ = "booking_requests"
    __table_args__ = (CheckConstraint("preferred_ends_at > preferred_starts_at"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(40), index=True)
    line_id: Mapped[str] = mapped_column(String(120), default="")
    service_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clinic_services.id"))
    service_name: Mapped[str] = mapped_column(String(200))
    preferred_starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    preferred_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    note: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

