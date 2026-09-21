from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.schemas.identity import LoginInput


class ForgotPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return LoginInput.normalize_email(value)


class ResetPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: SecretStr
    new_password: SecretStr

    @field_validator("token")
    @classmethod
    def token_length(cls, value):
        if not 32 <= len(value.get_secret_value()) <= 128:
            raise ValueError("Invalid reset token")
        return value

    @field_validator("new_password")
    @classmethod
    def password_length(cls, value):
        raw = value.get_secret_value()
        if len(raw) < 12 or len(raw.encode()) > 72:
            raise ValueError("Use at least 12 characters and at most 72 UTF-8 bytes")
        return value
