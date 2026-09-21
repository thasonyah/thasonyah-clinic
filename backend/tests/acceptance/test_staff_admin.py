import secrets
import uuid

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_staff_status_and_self_guard():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["admin", "reception"]
        ]
        db.add_all(users)
        db.commit()
        rows = [(str(u.id), u.email) for u in users]
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                    "access_token"
                ]
            }
            for _, email in rows
        ]
        url = f"/api/v1/users/{rows[1][0]}/status"
        assert c.patch(url, headers=headers[1], json={"active": False}).status_code == 403
        assert (
            c.patch(
                f"/api/v1/users/{rows[0][0]}/status", headers=headers[0], json={"active": False}
            ).status_code
            == 409
        )
        assert c.patch(url, headers=headers[0], json={"active": False}).status_code == 200
        assert c.get("/api/v1/auth/me", headers=headers[1]).status_code == 401
        assert c.patch(url, headers=headers[0], json={"active": True}).status_code == 200
        assert c.get("/api/v1/auth/me", headers=headers[1]).status_code == 401
        audit = c.get("/api/v1/audit", headers=headers[0])
        assert audit.status_code == 200
        assert any(
            a["action"] == "user.status" and a["target_id"] == rows[1][0] for a in audit.json()
        )
    limiter.reset()
