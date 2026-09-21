import uuid
from datetime import timedelta
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.schemas.records import VersionInput


class ResourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=150)


class ResourceOutput(ResourceInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    active: bool


class AppointmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    patient_id: uuid.UUID
    resource_id: uuid.UUID | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def valid_time(self):
        if not timedelta(0) < self.ends_at - self.starts_at <= timedelta(hours=8):
            raise ValueError("Appointment duration must be positive and no longer than 8 hours")
        return self


class AppointmentOutput(AppointmentInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    provider_id: uuid.UUID
    status: str
    version: int
    patient_name: str = ""


class AppointmentStatus(VersionInput):
    status: Literal["arrived", "in_service", "completed", "cancelled"]


class AppointmentMove(VersionInput):
    resource_id: uuid.UUID | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def valid_time(self):
        if not timedelta(0) < self.ends_at - self.starts_at <= timedelta(hours=8):
            raise ValueError("Duration must be positive and at most 8 hours")
        return self
