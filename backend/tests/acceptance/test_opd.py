import secrets
import uuid

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_structured_opd_amendment_and_versions():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "practitioner"]
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
            "/api/v1/patients",
            headers=h[0],
            json={
                "name": "OPD สมมติ",
                "provider_id": ids[1],
                "address": "ที่อยู่ทดสอบ",
                "allergies": "ยังไม่ทราบ",
            },
        )
        assert p.status_code == 201
        pid = p.json()["id"]
        data = {
            "chief_complaint": "อาการทดสอบ",
            "opd": {"น้ำหนัก (กก.)": "60", "ส่วนสูง (ซม.)": "160", "รูปธาตุ · เกศา": "ยังไม่ได้ประเมิน"},
        }
        v = c.post(f"/api/v1/patients/{pid}/visits", headers=h[1], json=data)
        assert v.status_code == 201
        vid = v.json()["id"]
        assert v.json()["bmi"] == "23.44"
        assert (
            c.patch(
                f"/api/v1/visits/{vid}", headers=h[1], json={**data, "expected_version": 1}
            ).status_code
            == 200
        )
        assert (
            c.patch(
                f"/api/v1/visits/{vid}", headers=h[1], json={**data, "expected_version": 1}
            ).status_code
            == 409
        )
        assert (
            c.post(
                f"/api/v1/visits/{vid}/amendments",
                headers=h[1],
                json={"reason": "แก้ไข", "text": "เพิ่มเติม"},
            ).status_code
            == 409
        )
        assert (
            c.post(
                f"/api/v1/visits/{vid}/sign", headers=h[1], json={"expected_version": 2}
            ).status_code
            == 200
        )
        a = {"reason": "เพิ่มเติมผลติดตาม", "text": "ข้อมูลสมมติเท่านั้น"}
        assert c.post(f"/api/v1/visits/{vid}/amendments", headers=h[2], json=a).status_code == 404
        assert c.post(f"/api/v1/visits/{vid}/amendments", headers=h[1], json=a).status_code == 201
        history = c.get(f"/api/v1/visits/{vid}/amendments", headers=h[1]).json()
        assert len(history) == 1 and history[0]["text"] == a["text"]
        saved = c.get(f"/api/v1/patients/{pid}/visits", headers=h[1]).json()[0]
        assert saved["opd"] == data["opd"]
        assert (
            c.post(
                f"/api/v1/patients/{pid}/visits",
                headers=h[1],
                json={**data, "opd": {"น้ำหนัก (กก.)": "-1"}},
            ).status_code
            == 422
        )
    limiter.reset()


def test_patient_correction_rejects_stale_version():
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
        data = {"name": "ทะเบียนสมมติ", "provider_id": ids[1]}
        p = c.post("/api/v1/patients", headers=h[0], json=data).json()
        changed = {**data, "allergies": "แก้ข้อมูลสมมติ", "expected_version": 1}
        url = f"/api/v1/patients/{p['id']}"
        assert c.patch(url, headers=h[1], json=changed).status_code == 403
        assert c.patch(url, headers=h[0], json=changed).status_code == 200
        assert c.patch(url, headers=h[0], json=changed).status_code == 409
        assert c.get(url, headers=h[1]).json()["allergies"] == "แก้ข้อมูลสมมติ"
    limiter.reset()
