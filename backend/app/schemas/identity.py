import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Role = Literal["admin", "manager", "practitioner", "reception", "finance", "pharmacy"]


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().lower()
        if value.count("@") != 1 or any(c.isspace() for c in value):
            raise ValueError("Invalid email")
        return value

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if not 1 <= len(value.get_secret_value().encode()) <= 72:
            raise ValueError("Password must be 1–72 UTF-8 bytes")
        return value


class CreateUser(LoginInput):
    role: Role

    @field_validator("password")
    @classmethod
    def strong_password(cls, value):
        if len(value.get_secret_value()) < 12:
            raise ValueError("Use at least 12 characters")
        return value


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    role: Role
    active: bool


class MeOutput(UserOutput):
    permissions: list[str] = Field(default_factory=list)


class LoginOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_summary: UserOutput


class ChangePassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr
    new_password: SecretStr

    @field_validator("current_password", "new_password")
    @classmethod
    def bounded_password(cls, value):
        if not 1 <= len(value.get_secret_value().encode()) <= 72:
            raise ValueError("Password must be 1–72 UTF-8 bytes")
        return value

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value):
        if len(value.get_secret_value()) < 12:
            raise ValueError("Use at least 12 characters")
        return value


class UserStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool
