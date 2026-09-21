import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_count_is_idempotent_and_rejects_stale_quantity():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        u = User(
            email=f"{uuid.uuid4()}@example.test",
            role="pharmacy",
            password_hash=hash_password(password),
        )
        db.add(u)
        db.commit()
        email = u.email
    with TestClient(app) as c:
        h = {
            "Authorization": "Bearer "
            + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                "access_token"
            ]
        }
        med = c.post(
            "/api/v1/medicines", headers=h, json={"name": str(uuid.uuid4()), "unit": "หน่วย"}
        ).json()
        lot = c.post(
            "/api/v1/lots",
            headers=h,
            json={
                "medicine_id": med["id"],
                "lot_number": str(uuid.uuid4()),
                "expires_on": str(date.today() + timedelta(days=90)),
                "quantity": 10,
            },
        ).json()
        url = f"/api/v1/lots/{lot['id']}/adjust"
        payload = {
            "request_id": str(uuid.uuid4()),
            "expected_quantity": 10,
            "quantity": 7,
            "kind": "count",
            "reason": "ตรวจนับทดสอบ",
        }

        def adjust(data):
            with TestClient(app) as client:
                return client.post(url, headers=h, json=data)

        second = {**payload, "request_id": str(uuid.uuid4()), "quantity": 6}
        with ThreadPoolExecutor(2) as pool:
            result = list(pool.map(adjust, [payload, second]))
        assert sorted(r.status_code for r in result) == [200, 409]
        winner = next(r.json() for r in result if r.status_code == 200)
        original = payload if winner["quantity"] == 7 else second
        assert adjust(original).json()["quantity"] == winner["quantity"]
        movements = c.get(f"/api/v1/lots/{lot['id']}/movements", headers=h).json()
        assert sum(m["quantity"] for m in movements) == winner["quantity"]
        assert len(movements) == 2
    limiter.reset()
