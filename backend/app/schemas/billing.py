import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: uuid.UUID
    quantity: int = Field(ge=1, le=100)


class InvoiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visit_id: uuid.UUID
    items: list[InvoiceItem] = Field(min_length=1, max_length=50)


class MoneyEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: int
    amount: Decimal
    method: str
    actor_id: uuid.UUID | None
    reason: str
    created_at: datetime


class InvoiceOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: int
    visit_id: uuid.UUID
    patient_name: str
    items: list[dict]
    total: Decimal
    paid_total: Decimal
    refunded_total: Decimal
    due_total: Decimal
    payments: list[MoneyEntry]
    refunds: list[MoneyEntry]
    status: str
    created_at: datetime
    paid_at: datetime | None
    payment_method: str | None
    refunded_at: datetime | None
    refund_reason: str | None


class PaymentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: Literal["cash", "transfer", "card"]


class RefundInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: uuid.UUID
    reason: str = Field(min_length=1, max_length=1000)

    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    method: Literal["cash", "transfer", "card"] | None = None


class CashCloseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    counted_cash: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    note: str = Field(default="", max_length=1000)


class CashCloseOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    day: date
    actor_id: uuid.UUID | None
    expected_cash: Decimal
    counted_cash: Decimal
    difference: Decimal
    note: str
    channels: dict
    created_at: datetime
