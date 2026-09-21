import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

from app.services import zodiac


class PatientInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    birth_date: date | None = None
    birth_lunar_month: int | None = Field(default=None, ge=1, le=12)
    birth_lunar_phase: str | None = Field(default=None, max_length=20)
    gestation_months: int | None = Field(default=None, ge=1, le=12)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=2000)
    allergies: str = Field(default="", max_length=2000)
    emergency_contact: str = Field(default="", max_length=500)
    provider_id: uuid.UUID

    @field_validator("birth_date")
    @classmethod
    def not_future(cls, value):
        if value and value > datetime.now(ZoneInfo("Asia/Bangkok")).date():
            raise ValueError("Birth date cannot be in the future")
        return value

    @field_validator("birth_lunar_phase")
    @classmethod
    def valid_lunar_phase(cls, value):
        if value in (None, ""):
            return None
        if value not in zodiac.PHASES:
            raise ValueError("Birth lunar phase must be ข้างขึ้น or ข้างแรม")
        return value


class PatientUpdate(PatientInput):
    expected_version: int = Field(gt=0)


class PatientOutput(PatientInput):
    version: int
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID

    @computed_field
    @property
    def zodiac_snapshot(self) -> dict:
        return zodiac.calculate(
            self.birth_lunar_month, self.birth_lunar_phase, self.gestation_months, self.birth_date
        )


class VisitInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    chief_complaint: str = Field(min_length=1, max_length=2000)
    notes: str = Field(default="", max_length=20000)

    opd: dict[
        Annotated[str, StringConstraints(min_length=1, max_length=160)],
        Annotated[str, StringConstraints(max_length=5000)],
    ] = Field(default_factory=dict, max_length=250)

    @field_validator("opd")
    @classmethod
    def validate_opd(cls, value):
        if sum(len(k) + len(v) for k, v in value.items()) > 100000:
            raise ValueError("OPD too large")
        bounds = {
            "น้ำหนัก (กก.)": (0.1, 700),
            "ส่วนสูง (ซม.)": (10, 300),
            "ความดันตัวบน (mmHg)": (1, 350),
            "ความดันตัวล่าง (mmHg)": (1, 250),
            "คะแนนปวดหลังรับบริการ (0–10)": (0, 10),
            "คะแนนปวดก่อนรับบริการ (0–10)": (0, 10),
        }
        for key, (low, high) in bounds.items():
            if value.get(key):
                try:
                    number = Decimal(value[key])
                    if not number.is_finite() or not Decimal(str(low)) <= number <= Decimal(
                        str(high)
                    ):
                        raise ValueError("Value out of range")
                except InvalidOperation:
                    raise ValueError("Numeric value required") from None
        return value


class VersionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(gt=0)


class VisitUpdate(VisitInput, VersionInput):
    pass


class VisitOutput(VisitInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    version: int
    created_at: datetime
    signed_at: datetime | None

    @computed_field
    @property
    def bmi(self) -> str | None:
        if self.opd.get("น้ำหนัก (กก.)") and self.opd.get("ส่วนสูง (ซม.)"):
            height = Decimal(self.opd["ส่วนสูง (ซม.)"]) / 100
            return str((Decimal(self.opd["น้ำหนัก (กก.)"]) / height**2).quantize(Decimal("0.01")))
        return None


class AmendmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=1000)
    text: str = Field(min_length=1, max_length=20000)


class AmendmentOutput(AmendmentInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    visit_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime


class ConsentAttachmentOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    note: str
    uploaded_by: uuid.UUID
    created_at: datetime
