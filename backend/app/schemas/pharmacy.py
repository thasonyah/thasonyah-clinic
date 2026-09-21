import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MedicineInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=40)


class MedicineOutput(MedicineInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    active: bool


class LotInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    medicine_id: uuid.UUID
    lot_number: str = Field(min_length=1, max_length=100)
    expires_on: date
    quantity: int = Field(ge=1, le=1000000)


class LotOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    medicine_id: uuid.UUID
    lot_number: str
    expires_on: date
    quantity: int


class PrescriptionItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    medicine_id: uuid.UUID
    quantity: int = Field(ge=1, le=1000000)
    instructions: str = Field(min_length=1, max_length=2000)


class PrescriptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visit_id: uuid.UUID
    items: list[PrescriptionItem] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def unique_medicines(self):
        if len({i.medicine_id for i in self.items}) != len(self.items):
            raise ValueError("Combine the quantity and instructions for each medicine")
        return self


class PrescriptionOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    visit_id: uuid.UUID
    patient_name: str
    allergies: str
    current_allergies: str = ""
    remaining: list[dict] = Field(default_factory=list)
    allocations: list[dict] = Field(default_factory=list)
    items: list[dict]
    status: str
    created_at: datetime
    dispensed_at: datetime | None


class DispenseItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    medicine_id: uuid.UUID
    quantity: int = Field(ge=1, le=1000000)


class DispenseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID

    items: list[DispenseItem] | None = Field(default=None, min_length=1, max_length=50)


class StockAdjustment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: uuid.UUID
    expected_quantity: int = Field(ge=0, le=1000000)
    quantity: int = Field(ge=0, le=1000000)
    kind: Literal["count", "return", "damage", "correction"]
    reason: str = Field(min_length=1, max_length=900)


class MovementOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lot_id: uuid.UUID
    prescription_id: uuid.UUID | None
    actor_id: uuid.UUID
    quantity: int
    balance: int | None
    reason: str
    created_at: datetime
