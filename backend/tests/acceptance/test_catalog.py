import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_catalog_persistence_permissions_and_concurrent_update():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    emails = [f"{uuid.uuid4()}@example.test" for _ in range(2)]
    with SessionLocal() as db:
        db.add_all(
            [
                User(email=email, role=role, password_hash=hash_password(password))
                for email, role in zip(emails, ["admin", "reception"])
            ]
        )
        db.commit()
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                    "access_token"
                ]
            }
            for email in emails
        ]
        payload = {"name": str(uuid.uuid4()), "price": "500.00", "minutes": 45}
        assert c.post("/api/v1/services", headers=headers[1], json=payload).status_code == 403
        created = c.post("/api/v1/services", headers=headers[0], json=payload)
        assert created.status_code == 201
        item = created.json()
        assert any(
            s["id"] == item["id"] for s in c.get("/api/v1/services", headers=headers[1]).json()
        )
        patch = dict(payload, active=False, expected_version=1)
        assert (
            c.patch("/api/v1/services/" + item["id"], headers=headers[1], json=patch).status_code
            == 403
        )

        def change(_):
            with TestClient(app) as client:
                return client.patch(
                    "/api/v1/services/" + item["id"], headers=headers[0], json=patch
                ).status_code

        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(change, range(10)))
        assert results.count(200) == 1
        assert results.count(409) == 9
        stored = next(
            s for s in c.get("/api/v1/services", headers=headers[0]).json() if s["id"] == item["id"]
        )
        assert stored["active"] is False and stored["version"] == 2
    limiter.reset()
