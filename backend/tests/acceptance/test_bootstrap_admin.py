import secrets
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.services.bootstrap import ensure_bootstrap_admin
from app.services.identity import hash_password


def test_bootstrap_admin_created_once(monkeypatch):
    with SessionLocal() as db:
        existing_admin_ids = list(db.scalars(select(User.id).where(User.role == "admin", User.active.is_(True))))
        for user_id in existing_admin_ids:
            db.get(User, user_id).active = False
        db.commit()

    settings = get_settings()
    email = f"bootstrap-{uuid.uuid4()}@example.test"
    password = secrets.token_urlsafe(24)
    monkeypatch.setattr(settings, "bootstrap_admin_email", email)
    monkeypatch.setattr(settings, "bootstrap_admin_password", type("Secret", (), {"get_secret_value": lambda self: password})())

    try:
        assert ensure_bootstrap_admin() is True
        assert ensure_bootstrap_admin() is False
    finally:
        with SessionLocal() as db:
            for user_id in existing_admin_ids:
                user = db.get(User, user_id)
                if user:
                    user.active = True
            db.commit()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.role == "admin"
        assert user.active is True

    with TestClient(app) as client:
        result = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert result.status_code == 200, result.text


def test_bootstrap_admin_does_not_replace_existing_admin(monkeypatch):
    existing_password = secrets.token_urlsafe(24)
    existing_email = f"existing-{uuid.uuid4()}@example.test"
    with SessionLocal() as db:
        db.add(User(email=existing_email, role="admin", password_hash=hash_password(existing_password)))
        db.commit()

    settings = get_settings()
    requested_email = f"bootstrap-{uuid.uuid4()}@example.test"
    requested_password = secrets.token_urlsafe(24)
    monkeypatch.setattr(settings, "bootstrap_admin_email", requested_email)
    monkeypatch.setattr(settings, "bootstrap_admin_password", type("Secret", (), {"get_secret_value": lambda self: requested_password})())

    assert ensure_bootstrap_admin() is False
    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.email == requested_email)) is None
