import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_booking_race_retry_queue_and_roles():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "admin", "practitioner"]
        ]
        db.add_all(users)
        db.commit()
        ids = [str(u.id) for u in users]
        emails = [u.email for u in users]
    with TestClient(app) as c:
        h = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": e, "password": password}).json()[
                    "access_token"
                ]
            }
            for e in emails
        ]
        p = c.post(
            "/api/v1/patients", headers=h[0], json={"name": "นัดสมมติ", "provider_id": ids[1]}
        ).json()
        resource = c.post("/api/v1/resources", headers=h[2], json={"name": str(uuid.uuid4())})
        assert resource.status_code == 201
        start = datetime.now(timezone.utc) + timedelta(days=2)
        payload = {
            "patient_id": p["id"],
            "resource_id": resource.json()["id"],
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=1)).isoformat(),
            "request_id": str(uuid.uuid4()),
        }

        def book(data):
            with TestClient(app) as client:
                return client.post("/api/v1/appointments", headers=h[0], json=data)

        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(book, [payload, {**payload, "request_id": str(uuid.uuid4())}]))
        assert sorted(r.status_code for r in results) == [201, 409]
        created = next(r.json() for r in results if r.status_code == 201)
        retry = {**payload, "request_id": created["request_id"]}
        assert book(retry).json()["id"] == created["id"]
        aid = created["id"]
        url = f"/api/v1/appointments/{aid}/status"
        assert (
            c.patch(
                url, headers=h[0], json={"status": "completed", "expected_version": 1}
            ).status_code
            == 409
        )
        assert (
            c.patch(
                url, headers=h[0], json={"status": "arrived", "expected_version": 1}
            ).status_code
            == 200
        )
        assert (
            c.patch(
                url, headers=h[3], json={"status": "in_service", "expected_version": 2}
            ).status_code
            == 404
        )
        assert (
            c.patch(
                url, headers=h[1], json={"status": "in_service", "expected_version": 2}
            ).status_code
            == 200
        )
        assert (
            c.patch(
                url, headers=h[1], json={"status": "completed", "expected_version": 2}
            ).status_code
            == 409
        )
        assert (
            c.patch(
                url, headers=h[1], json={"status": "completed", "expected_version": 3}
            ).status_code
            == 200
        )
        assert c.get("/api/v1/appointments", headers=h[2]).status_code == 403
    limiter.reset()


def test_reschedule_conflict_keeps_original():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner"]
        ]
        db.add_all(users)
        db.commit()
        provider_id, email = str(users[1].id), users[0].email
    with TestClient(app) as c:
        h = {
            "Authorization": "Bearer "
            + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                "access_token"
            ]
        }
        p = c.post(
            "/api/v1/patients", headers=h, json={"name": "เลื่อนนัดสมมติ", "provider_id": provider_id}
        ).json()
        start = datetime.now(timezone.utc) + timedelta(days=3)

        def data(offset):
            return {
                "patient_id": p["id"],
                "request_id": str(uuid.uuid4()),
                "starts_at": (start + timedelta(hours=offset)).isoformat(),
                "ends_at": (start + timedelta(hours=offset + 1)).isoformat(),
            }

        a = c.post("/api/v1/appointments", headers=h, json=data(0)).json()
        b = c.post("/api/v1/appointments", headers=h, json=data(2)).json()
        moved = {
            "starts_at": b["starts_at"],
            "ends_at": b["ends_at"],
            "resource_id": None,
            "expected_version": 1,
        }
        assert c.patch(f"/api/v1/appointments/{a['id']}", headers=h, json=moved).status_code == 409
        thai_day = start.astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat()
        original = c.get("/api/v1/appointments", headers=h, params={"day": thai_day}).json()
        assert next(x for x in original if x["id"] == a["id"])["starts_at"] == a["starts_at"]
        moved.update(
            starts_at=(start + timedelta(hours=4)).isoformat(),
            ends_at=(start + timedelta(hours=5)).isoformat(),
        )
        r = c.patch(f"/api/v1/appointments/{a['id']}", headers=h, json=moved)
        assert r.status_code == 200 and r.json()["version"] == 2
    limiter.reset()
