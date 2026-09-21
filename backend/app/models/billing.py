import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Identity, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, Identity(), unique=True)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), unique=True)
    patient_name: Mapped[str] = mapped_column(String(200))
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    items: Mapped[list] = mapped_column(JSONB)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="outstanding")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_request: Mapped[uuid.UUID | None] = mapped_column(unique=True)
    payment_method: Mapped[str | None] = mapped_column(String(20))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refund_request: Mapped[uuid.UUID | None] = mapped_column(unique=True)
    refund_reason: Mapped[str | None] = mapped_column(String(1000))

    payments: Mapped[list["PaymentReceipt"]] = relationship(
        lazy="selectin", order_by="PaymentReceipt.number"
    )
    refunds: Mapped[list["PaymentRefund"]] = relationship(
        lazy="selectin", order_by="PaymentRefund.number"
    )

    @property
    def paid_total(self):
        return sum((p.amount for p in self.payments), Decimal("0.00"))

    @property
    def refunded_total(self):
        return sum((p.amount for p in self.refunds), Decimal("0.00"))

    @property
    def due_total(self):
        return max(Decimal("0.00"), self.total - self.paid_total)


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, Identity(), unique=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    request_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PaymentRefund(Base):
    __tablename__ = "payment_refunds"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, Identity(), unique=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    request_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CashClose(Base):
    __tablename__ = "cash_closes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    expected_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    counted_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    difference: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    note: Mapped[str] = mapped_column(String(1000), default="")
    channels: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
