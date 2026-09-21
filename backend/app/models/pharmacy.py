import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    unit: Mapped[str] = mapped_column(String(40))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockLot(Base):
    __tablename__ = "stock_lots"
    __table_args__ = (
        UniqueConstraint("medicine_id", "lot_number"),
        CheckConstraint("quantity >= 0"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    medicine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicines.id"), index=True)
    lot_number: Mapped[str] = mapped_column(String(100))
    expires_on: Mapped[date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)


class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index(
            "uq_active_prescription_visit",
            "visit_id",
            unique=True,
            postgresql_where=text("status != 'cancelled'"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"))
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    patient_name: Mapped[str] = mapped_column(String(200))
    allergies: Mapped[str] = mapped_column(String(2000))
    items: Mapped[list] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="prescribed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dispensed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispense_request: Mapped[uuid.UUID | None] = mapped_column(unique=True)


class DispenseBatch(Base):
    __tablename__ = "dispense_batches"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id"))
    quantities: Mapped[dict] = mapped_column(JSONB)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockMovement(Base):
    __tablename__ = "stock_movements"
    request_id: Mapped[uuid.UUID | None] = mapped_column(unique=True)
    balance: Mapped[int | None] = mapped_column(Integer)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("dispense_batches.id"))
    lot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stock_lots.id"))
    prescription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prescriptions.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
