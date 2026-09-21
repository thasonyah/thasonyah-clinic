import secrets

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_rejects_non_postgres():
    with pytest.raises(ValidationError, match="PostgreSQL is required"):
        Settings(database_url="sqlite://", jwt_secret=secrets.token_urlsafe(48))


def test_normalizes_postgres_driver():
    settings = Settings(
        database_url="postgresql://localhost/clinic", jwt_secret=secrets.token_urlsafe(48)
    )
    assert settings.sqlalchemy_url.drivername == "postgresql+psycopg"
