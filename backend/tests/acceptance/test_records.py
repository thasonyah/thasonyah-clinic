import secrets
import uuid

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def test_records_scope_and_signed_immutability():
    limiter.reset()


def test_consent_attachment_upload_list_and_download():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test",
                role=role,
                password_hash=hash_password(password),
            )
            for role in ["reception", "practitioner", "practitioner"]
        ]
        db.add_all(users)
        db.commit()
        identities = [(str(u.id), u.email) for u in users]
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                    "access_token"
                ]
            }
            for _, email in identities
        ]
        patient = c.post(
            "/api/v1/patients",
            headers=headers[0],
            json={"name": "แนบใบยินยอมสมมติ", "provider_id": identities[1][0]},
        ).json()
        visit = c.post(
            f"/api/v1/patients/{patient['id']}/visits",
            headers=headers[1],
            json={"chief_complaint": "ขอรับบริการ"},
        ).json()
        payload = b"%PDF-1.4 fictional consent"
        uploaded = c.post(
            f"/api/v1/patients/{patient['id']}/consents",
            headers=headers[0],
            data={"visit_id": visit["id"], "note": "ยินยอมรับบริการทดสอบ"},
            files={"file": ("consent.pdf", payload, "application/pdf")},
        )
        assert uploaded.status_code == 201
        body = uploaded.json()
        assert body["filename"] == "consent.pdf"
        assert body["size_bytes"] == len(payload)
        assert len(body["sha256"]) == 64
        listing = c.get(f"/api/v1/patients/{patient['id']}/consents", headers=headers[1])
        assert listing.status_code == 200
        assert listing.json()[0]["id"] == body["id"]
        download = c.get(
            f"/api/v1/patients/{patient['id']}/consents/{body['id']}", headers=headers[1]
        )
        assert download.status_code == 200
        assert download.content == payload
        out_of_scope = c.get(f"/api/v1/patients/{patient['id']}/consents", headers=headers[2])
        assert out_of_scope.status_code == 404
        too_big = c.post(
            f"/api/v1/patients/{patient['id']}/consents",
            headers=headers[0],
            files={"file": ("big.pdf", b"x" * (5 * 1024 * 1024 + 1), "application/pdf")},
        )
        assert too_big.status_code == 422
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test",
                role=role,
                password_hash=hash_password(password),
            )
            for role in ["reception", "practitioner", "practitioner", "admin"]
        ]
        db.add_all(users)
        db.commit()
        identities = [(str(u.id), u.email) for u in users]
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                    "access_token"
                ]
            }
            for _, email in identities
        ]
        payload = {"name": "ผู้ป่วยทดสอบ", "birth_date": "1990-01-01", "provider_id": identities[1][0]}
        assert c.post("/api/v1/patients", headers=headers[3], json=payload).status_code == 403
        p = c.post("/api/v1/patients", headers=headers[0], json=payload)
        assert p.status_code == 201
        pid = p.json()["id"]
        assert c.get(f"/api/v1/patients/{pid}", headers=headers[2]).status_code == 404
        assert c.get(f"/api/v1/patients/{pid}", headers=headers[1]).status_code == 200
        assert c.get(f"/api/v1/patients/{pid}/visits", headers=headers[0]).status_code == 403
        visit = c.post(
            f"/api/v1/patients/{pid}/visits",
            headers=headers[1],
            json={"chief_complaint": "ทดสอบ", "notes": "ข้อมูลสมมติ"},
        )
        assert visit.status_code == 201
        vid = visit.json()["id"]
        assert (
            c.post(
                f"/api/v1/visits/{vid}/sign", headers=headers[2], json={"expected_version": 1}
            ).status_code
            == 404
        )
        signed = c.post(
            f"/api/v1/visits/{vid}/sign", headers=headers[1], json={"expected_version": 1}
        )
        assert signed.status_code == 200
        assert signed.json()["signed_at"]
        assert (
            c.patch(
                f"/api/v1/visits/{vid}",
                headers=headers[1],
                json={"chief_complaint": "เปลี่ยน", "notes": "", "expected_version": 2},
            ).status_code
            == 409
        )
        assert (
            c.get(f"/api/v1/patients/{pid}/visits", headers=headers[1]).json()[0]["notes"]
            == "ข้อมูลสมมติ"
        )
    limiter.reset()


def test_patient_zodiac_inputs_calculate_birth_and_conception_elements():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test",
                role=role,
                password_hash=hash_password(password),
            )
            for role in ["reception", "practitioner"]
        ]
        db.add_all(users)
        db.commit()
        identities = [(str(u.id), u.email) for u in users]
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                    "access_token"
                ]
            }
            for _, email in identities
        ]
        created = c.post(
            "/api/v1/patients",
            headers=headers[0],
            json={
                "name": "จักรราศีตัวอย่าง",
                "birth_date": "1979-11-10",
                "gestation_months": 9,
                "provider_id": identities[1][0],
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["birth_lunar_month"] == 12
        assert body["birth_lunar_phase"] == "ข้างแรม"
        snapshot = body["zodiac_snapshot"]
        assert snapshot["status"] == "calculated"
        assert snapshot["lunar_source"] == "pythaidate-0.2.0 CsDate"
        assert snapshot["auto_lunar"]["lunar_day"] == 6
        assert snapshot["birth_element"] == {
            "element": "ธาตุน้ำ",
            "condition": "เตโชพิการ",
            "mixed_with": "กำเดาระคน",
        }
        assert snapshot["conception_month"] == 3
        assert snapshot["conception_element"]["waxing"] == {
            "element": "ธาตุดิน",
            "condition": "วาโยพิการ",
            "mixed_with": "สุมนาวาตะระคน",
        }
        assert snapshot["conception_element"]["waning"] == {
            "element": "ธาตุดิน",
            "condition": "อาโปพิการ",
            "mixed_with": "คูถเสมหะระคน",
        }
        invalid = c.post(
            "/api/v1/patients",
            headers=headers[0],
            json={
                "name": "ข้อมูลผิด",
                "birth_lunar_month": 13,
                "birth_lunar_phase": "ข้างขึ้น",
                "gestation_months": 9,
                "provider_id": identities[1][0],
            },
        )
        assert invalid.status_code == 422
    limiter.reset()
