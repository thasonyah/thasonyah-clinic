import secrets
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_reset_single_use_and_revocation():
    limiter.reset()
    email = f"{uuid.uuid4()}@example.test"
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        db.add(User(email=email, role="admin", password_hash=hash_password(password)))
        db.commit()
    with TestClient(app) as c:
        auth = c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
        headers = {"Authorization": "Bearer " + auth["access_token"]}
        with (
            patch("app.services.password_reset.send_reset_email") as send,
            patch("app.services.password_reset.mail_configured", return_value=True),
        ):
            known = c.post("/api/v1/auth/forgot-password", json={"email": email})
            assert known.status_code == 202
            token = send.call_args.args[1]
            unknown = c.post(
                "/api/v1/auth/forgot-password", json={"email": f"{uuid.uuid4()}@example.test"}
            )
            assert known.json() == unknown.json()
            assert send.call_count == 1
        replacement = secrets.token_urlsafe(24)
        body = {"token": token, "new_password": replacement}
        assert c.post("/api/v1/auth/reset-password", json=body).status_code == 204
        assert c.post("/api/v1/auth/reset-password", json=body).status_code == 400
        assert c.get("/api/v1/auth/me", headers=headers).status_code == 401
        assert (
            c.post("/api/v1/auth/login", json={"email": email, "password": password}).status_code
            == 401
        )
        assert (
            c.post("/api/v1/auth/login", json={"email": email, "password": replacement}).status_code
            == 200
        )
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            assert user.password_hash != replacement
    limiter.reset()


def test_expired_reset_and_missing_mail_config():
    import hashlib
    from datetime import datetime, timedelta, timezone

    from app.models.identity import PasswordReset

    limiter.reset()
    token = secrets.token_urlsafe(32)
    with SessionLocal() as db:
        user = User(
            email=f"{uuid.uuid4()}@example.test",
            role="admin",
            password_hash=hash_password(secrets.token_urlsafe(24)),
        )
        db.add(user)
        db.flush()
        db.add(
            PasswordReset(
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        db.commit()
    with TestClient(app) as c:
        assert (
            c.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": secrets.token_urlsafe(24)},
            ).status_code
            == 400
        )
        assert (
            c.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": secrets.token_urlsafe(32),
                    "new_password": secrets.token_urlsafe(24),
                },
            ).status_code
            == 400
        )
        with patch("app.services.password_reset.mail_configured", return_value=False):
            assert (
                c.post(
                    "/api/v1/auth/forgot-password", json={"email": "nobody@example.test"}
                ).status_code
                == 503
            )
    limiter.reset()


def test_two_simultaneous_resets_only_one_succeeds():
    import hashlib
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timedelta, timezone

    from app.models.identity import PasswordReset

    limiter.reset()
    token = secrets.token_urlsafe(32)
    with SessionLocal() as db:
        user = User(
            email=f"{uuid.uuid4()}@example.test",
            role="admin",
            password_hash=hash_password(secrets.token_urlsafe(24)),
        )
        db.add(user)
        db.flush()
        db.add(
            PasswordReset(
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )
        )
        db.commit()

    def reset(_):
        with TestClient(app) as c:
            return c.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": secrets.token_urlsafe(24)},
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reset, range(2)))
    assert sorted(results) == [204, 400]
    limiter.reset()
