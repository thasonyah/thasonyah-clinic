import uuid
from datetime import timedelta
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.schemas.records import VersionInput


class PublicServiceOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    price: float
    minutes: int


class BookingRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: uuid.UUID
    full_name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=8, max_length=40, pattern=r"^[0-9+()\-\s]+$")
    line_id: str = Field(default="", max_length=120)
    service_id: uuid.UUID | None = None
    service_name: str = Field(default="", max_length=200)
    preferred_starts_at: AwareDatetime
    preferred_ends_at: AwareDatetime
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def valid_time(self):
        duration = self.preferred_ends_at - self.preferred_starts_at
        if not timedelta(0) < duration <= timedelta(hours=8):
            raise ValueError("Booking duration must be positive and no longer than 8 hours")
        return self


class BookingRequestOutput(BookingRequestInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    version: int
    created_at: AwareDatetime


class BookingRequestStatus(VersionInput):
    status: Literal["contacted", "cancelled"]
