import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_lunar_month: Mapped[int | None] = mapped_column(Integer)
    birth_lunar_phase: Mapped[str | None] = mapped_column(String(20))
    gestation_months: Mapped[int | None] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(String(2000), default="")
    allergies: Mapped[str] = mapped_column(String(2000), default="")
    emergency_contact: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class Visit(Base):
    __tablename__ = "visits"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    chief_complaint: Mapped[str] = mapped_column(String(2000))
    opd: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VisitAmendment(Base):
    __tablename__ = "visit_amendments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(1000))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConsentAttachment(Base):
    __tablename__ = "consent_attachments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    visit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("visits.id"), index=True)
    filename: Mapped[str] = mapped_column(String(240))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    note: Mapped[str] = mapped_column(String(1000), default="")
    data: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
