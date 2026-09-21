import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=150)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    minutes: int = Field(gt=0, le=1440, strict=True)


class ServiceUpdate(ServiceInput):
    active: bool
    expected_version: int = Field(gt=0)


class ServiceOutput(ServiceInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    active: bool
    version: int
