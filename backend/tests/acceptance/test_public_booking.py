import secrets
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.catalog import ClinicService
from app.models.identity import User
from app.routers.auth import limiter
from app.services.identity import hash_password


def _next_open_start():
    zone = ZoneInfo("Asia/Bangkok")
    value = datetime.now(zone).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    while value.weekday() not in {0, 4, 5, 6}:
        value += timedelta(days=1)
    return value


def test_public_booking_request_is_visible_to_reception():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        user = User(
            email=f"{uuid.uuid4()}@example.test",
            role="reception",
            password_hash=hash_password(password),
        )
        service = ClinicService(name=str(uuid.uuid4()), price="450.00", minutes=60, active=True)
        db.add_all([user, service])
        db.commit()
        email = user.email
        service_id = str(service.id)
    start = _next_open_start()
    with TestClient(app) as c:
        public_services = c.get("/api/v1/public/services")
        assert public_services.status_code == 200
        assert any(item["id"] == service_id for item in public_services.json())
        booking = c.post(
            "/api/v1/public/bookings",
            json={
                "request_id": str(uuid.uuid4()),
                "full_name": "คนไข้ทดสอบ",
                "phone": "0822035330",
                "line_id": "patient-line",
                "service_id": service_id,
                "preferred_starts_at": start.isoformat(),
                "preferred_ends_at": (start + timedelta(minutes=60)).isoformat(),
                "note": "ปวดบ่า",
            },
        )
        assert booking.status_code == 201
        assert booking.json()["status"] == "pending"
        headers = {
            "Authorization": "Bearer "
            + c.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
                "access_token"
            ]
        }
        requests = c.get("/api/v1/booking-requests", headers=headers, params={"day": start.date()})
        assert requests.status_code == 200
        assert requests.json()[0]["full_name"] == "คนไข้ทดสอบ"
        changed = c.patch(
            f"/api/v1/booking-requests/{booking.json()['id']}/status",
            headers=headers,
            json={"status": "contacted", "expected_version": 1},
        )
        assert changed.status_code == 200
        assert changed.json()["status"] == "contacted"
    limiter.reset()


def test_reception_confirms_public_booking_into_patient_and_appointment():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        reception = User(
            email=f"{uuid.uuid4()}@example.test",
            role="reception",
            password_hash=hash_password(password),
        )
        practitioner = User(
            email=f"{uuid.uuid4()}@example.test",
            role="practitioner",
            password_hash=hash_password(secrets.token_urlsafe(24)),
        )
        service = ClinicService(name=str(uuid.uuid4()), price="650.00", minutes=60, active=True)
        db.add_all([reception, practitioner, service])
        db.commit()
        reception_email = reception.email
        practitioner_id = str(practitioner.id)
        service_id = str(service.id)

    start = _next_open_start() + timedelta(hours=1)
    with TestClient(app) as c:
        booking = c.post(
            "/api/v1/public/bookings",
            json={
                "request_id": str(uuid.uuid4()),
                "full_name": "คนไข้ยืนยันนัด",
                "phone": "0822035331",
                "line_id": "patient-confirm",
                "service_id": service_id,
                "preferred_starts_at": start.isoformat(),
                "preferred_ends_at": (start + timedelta(minutes=60)).isoformat(),
                "note": "ต้องการยืนยันนัด",
            },
        )
        assert booking.status_code == 201
        headers = {
            "Authorization": "Bearer "
            + c.post(
                "/api/v1/auth/login", json={"email": reception_email, "password": password}
            ).json()["access_token"]
        }

        confirmed = c.post(
            f"/api/v1/booking-requests/{booking.json()['id']}/confirm",
            headers=headers,
            json={"provider_id": practitioner_id, "expected_version": 1},
        )
        assert confirmed.status_code == 200
        body = confirmed.json()
        assert body["booking_request"]["status"] == "booked"
        assert body["patient"]["name"] == "คนไข้ยืนยันนัด"
        assert body["patient"]["phone"] == "0822035331"
        assert body["patient"]["provider_id"] == practitioner_id
        assert body["appointment"]["patient_id"] == body["patient"]["id"]
        assert body["appointment"]["patient_name"] == "คนไข้ยืนยันนัด"
        assert body["appointment"]["starts_at"] == start.isoformat()

        appointments = c.get("/api/v1/appointments", headers=headers, params={"day": start.date()})
        assert appointments.status_code == 200
        assert any(item["id"] == body["appointment"]["id"] for item in appointments.json())
    limiter.reset()
