from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    database_url: SecretStr
    jwt_secret: SecretStr
    resend_api_key: SecretStr | None = None
    reset_email_from: str | None = None
    reset_public_url: str | None = None
    access_token_minutes: int = Field(default=30, ge=1, le=60)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: SecretStr | None = None
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("reset_public_url")
    @classmethod
    def safe_reset_url(cls, value):
        from urllib.parse import urlsplit

        if value:
            url = urlsplit(value)
            if (
                url.scheme != "https"
                or not url.netloc
                or url.fragment
                or url.query
                or url.username
                or url.password
            ):
                raise ValueError("Use a fixed HTTPS reset page URL without query or fragment")
        return value

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr) -> SecretStr:
        if make_url(value.get_secret_value()).get_backend_name() != "postgresql":
            raise ValueError("PostgreSQL is required")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        return value

    @property
    def sqlalchemy_url(self):
        return make_url(self.database_url.get_secret_value()).set(drivername="postgresql+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()
