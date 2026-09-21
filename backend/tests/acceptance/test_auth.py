import secrets
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.services.identity import hash_password


def test_identity_lifecycle():
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test",
                role=role,
                password_hash=hash_password(password),
            )
            for role in ["admin", "practitioner", "reception", "finance", "pharmacy", "manager"]
        ]
        db.add_all(users)
        db.commit()
        emails = [u.email for u in users]
    with TestClient(app) as client:
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/api/v1/users").status_code == 401
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"email": emails[0], "password": secrets.token_urlsafe(20)},
            ).status_code
            == 401
        )
        headers = []
        for email in emails:
            result = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            assert result.status_code == 200, result.text
            assert "password_hash" not in result.text
            headers.append({"Authorization": f"Bearer {result.json()['access_token']}"})
        for header in headers[1:]:
            assert client.get("/api/v1/users", headers=header).status_code == 403
            assert (
                client.post(
                    "/api/v1/users",
                    headers=header,
                    json={
                        "email": f"{uuid.uuid4()}@example.test",
                        "password": password,
                        "role": "admin",
                    },
                ).status_code
                == 403
            )
        assert client.get("/api/v1/users", headers=headers[0]).status_code == 200
        me = client.get("/api/v1/auth/me", headers=headers[0]).json()
        assert "clinical.read" not in me["permissions"]
        created = client.post(
            "/api/v1/users",
            headers=headers[0],
            json={
                "email": f"{uuid.uuid4()}@example.test",
                "password": password,
                "role": "reception",
            },
        )
        assert created.status_code == 201
        assert "password" not in created.text
        assert client.post("/api/v1/auth/logout", headers=headers[0]).status_code == 204
        assert client.get("/api/v1/auth/me", headers=headers[0]).status_code == 401
        assert (
            client.post(
                "/api/v1/auth/change-password",
                headers=headers[1],
                json={"current_password": password, "new_password": secrets.token_urlsafe(24)},
            ).status_code
            == 204
        )
        assert client.get("/api/v1/auth/me", headers=headers[1]).status_code == 401
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == emails[2]))
            user.active = False
            db.commit()
        assert client.get("/api/v1/auth/me", headers=headers[2]).status_code == 401
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": emails[2], "password": password}
            ).status_code
            == 401
        )


def test_invalid_token_and_secret_redaction():
    with TestClient(app) as client:
        assert (
            client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code
            == 401
        )
        password = secrets.token_urlsafe(90)
        result = client.post("/api/v1/auth/login", json={"email": "bad", "password": password})
        assert result.status_code == 422
        assert password not in result.text


def test_login_rate_limit():
    from app.routers.auth import limiter

    limiter.reset()
    with TestClient(app) as client:
        results = [
            client.post(
                "/api/v1/auth/login",
                json={"email": "missing@example.test", "password": secrets.token_urlsafe(20)},
            ).status_code
            for _ in range(11)
        ]
    assert results[:10] == [401] * 10
    assert results[10] == 429
    limiter.reset()


def test_session_expiry_and_duplicate_account():
    from datetime import datetime, timedelta, timezone

    from app.models.identity import LoginSession
    from app.routers.auth import limiter

    limiter.reset()
    password = secrets.token_urlsafe(24)
    email = f"{uuid.uuid4()}@example.test"
    with SessionLocal() as db:
        user = User(email=email, role="admin", password_hash=hash_password(password))
        db.add(user)
        db.commit()
        uid = user.id
    with TestClient(app) as client:
        result = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        header = {"Authorization": f"Bearer {result.json()['access_token']}"}
        assert (
            client.post(
                "/api/v1/users",
                headers=header,
                json={"email": email.upper(), "password": password, "role": "admin"},
            ).status_code
            == 409
        )
        with SessionLocal() as db:
            session = db.scalar(select(LoginSession).where(LoginSession.user_id == uid))
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        assert client.get("/api/v1/auth/me", headers=header).status_code == 401
    limiter.reset()
