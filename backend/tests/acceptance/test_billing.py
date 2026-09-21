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


def test_invoice_snapshot_concurrent_payment_and_refund():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "admin", "finance", "manager"]
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
            "/api/v1/patients", headers=h[0], json={"name": "ใบรับเงินสมมติ", "provider_id": ids[1]}
        ).json()
        v = c.post(
            f"/api/v1/patients/{p['id']}/visits", headers=h[1], json={"chief_complaint": "ทดสอบ"}
        ).json()
        c.post(f"/api/v1/visits/{v['id']}/sign", headers=h[1], json={"expected_version": 1})
        s = c.post(
            "/api/v1/services",
            headers=h[2],
            json={"name": str(uuid.uuid4()), "price": "125.50", "minutes": 30},
        ).json()
        data = {"visit_id": v["id"], "items": [{"service_id": s["id"], "quantity": 2}]}
        invoice = c.post("/api/v1/invoices", headers=h[1], json=data)
        assert invoice.status_code == 201
        iid = invoice.json()["id"]
        assert invoice.json()["total"] == "251.00"
        assert c.post("/api/v1/invoices", headers=h[1], json=data).status_code == 409
        assert (
            c.post(
                f"/api/v1/invoices/{iid}/payment",
                headers=h[0],
                json={"request_id": str(uuid.uuid4()), "amount": "251.00", "method": "cash"},
            ).status_code
            == 403
        )

        def pay(_):
            with TestClient(app) as client:
                return client.post(
                    f"/api/v1/invoices/{iid}/payment",
                    headers=h[3],
                    json={"request_id": str(uuid.uuid4()), "amount": "251.00", "method": "cash"},
                )

        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(pay, range(2)))
        assert sorted(r.status_code for r in results) == [200, 409]
        refund = {"request_id": str(uuid.uuid4()), "reason": "คืนเงินทดสอบ"}
        assert (
            c.post(f"/api/v1/invoices/{iid}/refund", headers=h[3], json=refund).status_code == 200
        )
        assert (
            c.post(f"/api/v1/invoices/{iid}/refund", headers=h[3], json=refund).status_code == 200
        )
        assert (
            c.post(
                f"/api/v1/invoices/{iid}/refund",
                headers=h[3],
                json={**refund, "request_id": str(uuid.uuid4())},
            ).status_code
            == 409
        )
        report = c.get("/api/v1/reports/daily", headers=h[4])
        assert report.status_code == 200 and "refunds" in report.json()
        assert c.get("/api/v1/invoices", headers=h[4]).status_code == 403
    limiter.reset()


def test_partial_payment_mixed_methods_and_partial_refund():
    limiter.reset()


def test_daily_cash_close_is_one_per_day_and_manager_visible():
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "admin", "finance", "manager"]
        ]
        db.add_all(users)
        db.commit()
        ids = [str(u.id) for u in users]
        emails = [u.email for u in users]
    with TestClient(app) as c:
        headers = [
            {
                "Authorization": "Bearer "
                + c.post("/api/v1/auth/login", json={"email": e, "password": password}).json()[
                    "access_token"
                ]
            }
            for e in emails
        ]
        patient = c.post(
            "/api/v1/patients",
            headers=headers[0],
            json={"name": "ปิดยอดเงินสดสมมติ", "provider_id": ids[1]},
        ).json()
        visit = c.post(
            f"/api/v1/patients/{patient['id']}/visits",
            headers=headers[1],
            json={"chief_complaint": "ทดสอบปิดยอด"},
        ).json()
        c.post(
            f"/api/v1/visits/{visit['id']}/sign",
            headers=headers[1],
            json={"expected_version": 1},
        )
        service = c.post(
            "/api/v1/services",
            headers=headers[2],
            json={"name": str(uuid.uuid4()), "price": "300.00", "minutes": 30},
        ).json()
        invoice = c.post(
            "/api/v1/invoices",
            headers=headers[1],
            json={"visit_id": visit["id"], "items": [{"service_id": service["id"], "quantity": 1}]},
        ).json()
        c.post(
            f"/api/v1/invoices/{invoice['id']}/payment",
            headers=headers[3],
            json={"request_id": str(uuid.uuid4()), "amount": "300.00", "method": "cash"},
        )
        report = c.get("/api/v1/reports/daily", headers=headers[4]).json()
        assert "cash" in report["channels"]
        close_day = (date(2099, 1, 1) + timedelta(days=uuid.uuid4().int % 30000)).isoformat()
        report = c.get(
            "/api/v1/reports/daily", headers=headers[4], params={"day": close_day}
        ).json()
        assert report["cash_close"] is None
        assert report["channels"] == {}
        close = c.post(
            "/api/v1/reports/daily/close",
            headers=headers[3],
            params={"day": close_day},
            json={"counted_cash": "290.00", "note": "เงินสดตั้งต้นสำหรับทดสอบ"},
        )
        assert close.status_code == 201
        assert close.json()["expected_cash"] == "0.00"
        assert close.json()["difference"] == "290.00"
        assert (
            c.post(
                "/api/v1/reports/daily/close",
                headers=headers[3],
                params={"day": close_day},
                json={"counted_cash": "300.00", "note": "ซ้ำ"},
            ).status_code
            == 409
        )
        manager_report = c.get(
            "/api/v1/reports/daily", headers=headers[4], params={"day": close_day}
        ).json()
        assert manager_report["cash_close"]["counted_cash"] == "290.00"
        assert (
            c.post(
                "/api/v1/reports/daily/close",
                headers=headers[4],
                params={"day": close_day},
                json={"counted_cash": "300.00"},
            ).status_code
            == 403
        )
    limiter.reset()
    password = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        users = [
            User(
                email=f"{uuid.uuid4()}@example.test", role=r, password_hash=hash_password(password)
            )
            for r in ["reception", "practitioner", "admin", "finance"]
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
            "/api/v1/patients", headers=h[0], json={"name": "แบ่งชำระสมมติ", "provider_id": ids[1]}
        ).json()
        v = c.post(
            f"/api/v1/patients/{p['id']}/visits", headers=h[1], json={"chief_complaint": "ทดสอบ"}
        ).json()
        c.post(f"/api/v1/visits/{v['id']}/sign", headers=h[1], json={"expected_version": 1})
        s = c.post(
            "/api/v1/services",
            headers=h[2],
            json={"name": str(uuid.uuid4()), "price": "600.00", "minutes": 30},
        ).json()
        invoice = c.post(
            "/api/v1/invoices",
            headers=h[1],
            json={"visit_id": v["id"], "items": [{"service_id": s["id"], "quantity": 1}]},
        ).json()
        url = f"/api/v1/invoices/{invoice['id']}"
        first = {"request_id": str(uuid.uuid4()), "amount": "100.00", "method": "cash"}
        paid = c.post(url + "/payment", headers=h[3], json=first)
        assert paid.status_code == 200
        assert paid.json()["due_total"] == "500.00"
        assert c.post(url + "/payment", headers=h[3], json=first).json()["paid_total"] == "100.00"
        paid = c.post(
            url + "/payment",
            headers=h[3],
            json={"request_id": str(uuid.uuid4()), "amount": "200.00", "method": "card"},
        )
        assert paid.json()["due_total"] == "300.00"
        refund = c.post(
            url + "/refund",
            headers=h[3],
            json={
                "request_id": str(uuid.uuid4()),
                "amount": "50.00",
                "method": "cash",
                "reason": "คืนบางส่วนทดสอบ",
            },
        )
        assert refund.status_code == 200
        assert refund.json()["refunded_total"] == "50.00"
        over = c.post(
            url + "/refund",
            headers=h[3],
            json={
                "request_id": str(uuid.uuid4()),
                "amount": "60.00",
                "method": "cash",
                "reason": "เกินยอดช่องทาง",
            },
        )
        assert over.status_code == 409
        paid = c.post(
            url + "/payment",
            headers=h[3],
            json={"request_id": str(uuid.uuid4()), "amount": "300.00", "method": "transfer"},
        )
        assert paid.json()["due_total"] == "0.00"
        assert len(paid.json()["payments"]) == 3
        assert len(set(r["number"] for r in paid.json()["payments"])) == 3
    limiter.reset()
