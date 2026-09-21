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


def test_pharmacy_expiry_concurrency_and_atomic_rollback():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "pharmacy"]
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
            "/api/v1/patients", headers=h[0], json={"name": "ยาสมมติ", "provider_id": ids[1]}
        ).json()
        meds = [
            c.post(
                "/api/v1/medicines", headers=h[2], json={"name": str(uuid.uuid4()), "unit": "หน่วย"}
            ).json()
            for _ in range(2)
        ]
        assert "id" in meds[0]

        def receive(mid, quantity, days):
            return c.post(
                "/api/v1/lots",
                headers=h[2],
                json={
                    "medicine_id": mid,
                    "lot_number": str(uuid.uuid4()),
                    "expires_on": str(date.today() + timedelta(days=days)),
                    "quantity": quantity,
                },
            )

        good = receive(meds[0]["id"], 5, 90).json()
        expired = receive(meds[0]["id"], 20, -1).json()

        def prescribe(items):
            v = c.post(
                f"/api/v1/patients/{p['id']}/visits",
                headers=h[1],
                json={"chief_complaint": "ทดสอบยา"},
            ).json()
            c.post(f"/api/v1/visits/{v['id']}/sign", headers=h[1], json={"expected_version": 1})
            return c.post(
                "/api/v1/prescriptions", headers=h[1], json={"visit_id": v["id"], "items": items}
            )

        line = {"medicine_id": meds[0]["id"], "quantity": 5, "instructions": "ข้อมูลสมมติ ไม่ใช้รักษา"}
        rx = prescribe([line]).json()
        assert "id" in rx

        def dispense(_):
            with TestClient(app) as client:
                return client.post(
                    f"/api/v1/prescriptions/{rx['id']}/dispense",
                    headers=h[2],
                    json={"request_id": str(uuid.uuid4())},
                )

        with ThreadPoolExecutor(2) as pool:
            result = list(pool.map(dispense, range(2)))
        assert sorted(r.status_code for r in result) == [200, 409]
        lots = c.get("/api/v1/lots", headers=h[2]).json()
        assert next(x for x in lots if x["id"] == good["id"])["quantity"] == 0
        assert next(x for x in lots if x["id"] == expired["id"])["quantity"] == 20
        fresh = receive(meds[0]["id"], 3, 90).json()
        failed = prescribe(
            [{**line, "quantity": 3}, {**line, "medicine_id": meds[1]["id"], "quantity": 1}]
        ).json()
        assert (
            c.post(
                f"/api/v1/prescriptions/{failed['id']}/dispense",
                headers=h[2],
                json={"request_id": str(uuid.uuid4())},
            ).status_code
            == 409
        )
        lots = c.get("/api/v1/lots", headers=h[2]).json()
        assert next(x for x in lots if x["id"] == fresh["id"])["quantity"] == 3
        assert (
            c.post(f"/api/v1/prescriptions/{failed['id']}/cancel", headers=h[1]).status_code == 200
        )
        replacement = c.post(
            "/api/v1/prescriptions",
            headers=h[1],
            json={"visit_id": failed["visit_id"], "items": [{**line, "quantity": 3}]},
        )
        assert replacement.status_code == 201
        assert replacement.json()["id"] != failed["id"]
        rxid = replacement.json()["id"]
        part = {
            "request_id": str(uuid.uuid4()),
            "items": [{"medicine_id": meds[0]["id"], "quantity": 2}],
        }
        partial = c.post(f"/api/v1/prescriptions/{rxid}/dispense", headers=h[2], json=part)
        assert partial.status_code == 200
        assert partial.json()["status"] == "partial"
        assert partial.json()["remaining"][0]["quantity"] == 1
        repeated = c.post(f"/api/v1/prescriptions/{rxid}/dispense", headers=h[2], json=part)
        assert repeated.json()["remaining"][0]["quantity"] == 1
        final = c.post(
            f"/api/v1/prescriptions/{rxid}/dispense",
            headers=h[2],
            json={"request_id": str(uuid.uuid4())},
        )
        assert final.json()["status"] == "dispensed"
        assert len(final.json()["allocations"]) == 2

        assert c.get("/api/v1/prescriptions", headers=h[0]).status_code == 403
    limiter.reset()
