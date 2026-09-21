"""Explicit fictional demo data. Never seed a local/production database."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.billing import Invoice
from app.models.catalog import ClinicService
from app.models.identity import User
from app.models.pharmacy import Medicine, Prescription, StockLot, StockMovement
from app.models.records import Patient, Visit
from app.models.scheduling import Appointment, Resource
from app.services.identity import hash_password
from scripts.seed import main as seed_services

ROLES = ("admin", "reception", "practitioner", "pharmacy", "finance", "manager")
DEMO_PASSWORD = "ClinicDemo2026!"


def uid(key):
    return uuid.uuid5(uuid.NAMESPACE_URL, "thasonyah-fictional-demo:" + key)


def main():
    database = get_settings().sqlalchemy_url.database or ""
    if not database.endswith(("_demo", "_test")):
        raise SystemExit("Refused: demo seed requires a database name ending _demo or _test.")
    seed_services()
    now = datetime.now(ZoneInfo("Asia/Bangkok"))
    with SessionLocal() as db:
        for role in ROLES:
            if not db.get(User, uid(role)):
                db.add(
                    User(
                        id=uid(role),
                        email=f"{role}@clinic.example.test",
                        role=role,
                        password_hash=hash_password(DEMO_PASSWORD),
                    )
                )
        db.flush()
        if not db.get(Resource, uid("bed")):
            db.add(Resource(id=uid("bed"), name="เตียงสาธิต A"))
        for i in range(1, 4):
            if not db.get(Patient, uid(f"patient{i}")):
                db.add(
                    Patient(
                        id=uid(f"patient{i}"),
                        name=f"คนไข้สมมติ {i} — ข้อมูลสาธิต",
                        birth_date=date(1990 + i, 1, 15),
                        phone="",
                        provider_id=uid("practitioner"),
                        created_by=uid("reception"),
                        allergies="ยังไม่ทราบ (ข้อมูลสมมติ)",
                        address="ข้อมูลสมมติสำหรับทดสอบเท่านั้น",
                        emergency_contact="",
                    )
                )
            db.flush()
            if not db.get(Visit, uid(f"visit{i}")):
                db.add(
                    Visit(
                        id=uid(f"visit{i}"),
                        patient_id=uid(f"patient{i}"),
                        provider_id=uid("practitioner"),
                        chief_complaint="อาการสมมติสำหรับทดลองบันทึก",
                        notes="ไม่ใช่ข้อมูลการรักษาจริง",
                        opd={
                            "น้ำหนัก (กก.)": "60",
                            "ส่วนสูง (ซม.)": "160",
                            "คำวินิจฉัยของแพทย์ (Dx)": "ข้อมูลสมมติ ยังไม่มีการวินิจฉัยจริง",
                        },
                        created_at=now - timedelta(days=i),
                        signed_at=now - timedelta(days=i),
                        version=2,
                    )
                )
            if not db.get(Appointment, uid(f"appt{i}")):
                start = now.replace(hour=8 + i, minute=0, second=0, microsecond=0)
                db.add(
                    Appointment(
                        id=uid(f"appt{i}"),
                        request_id=uid(f"booking{i}"),
                        patient_id=uid(f"patient{i}"),
                        provider_id=uid("practitioner"),
                        resource_id=uid("bed"),
                        starts_at=start,
                        ends_at=start + timedelta(minutes=45),
                        status="arrived" if i == 1 else "booked",
                        created_by=uid("reception"),
                    )
                )
        db.flush()
        service = db.scalar(
            select(ClinicService).where(ClinicService.active.is_(True)).order_by(ClinicService.name)
        )
        if service and not db.get(Invoice, uid("invoice")):
            db.add(
                Invoice(
                    id=uid("invoice"),
                    visit_id=uid("visit1"),
                    provider_id=uid("practitioner"),
                    patient_name="คนไข้สมมติ 1 — ข้อมูลสาธิต",
                    items=[
                        {
                            "service_id": str(service.id),
                            "name": service.name,
                            "quantity": 1,
                            "price": str(service.price),
                            "amount": str(service.price),
                        }
                    ],
                    total=Decimal(service.price),
                    created_at=now,
                    status="outstanding",
                )
            )
        for i in range(1, 3):
            if not db.get(Medicine, uid(f"med{i}")):
                db.add(
                    Medicine(id=uid(f"med{i}"), name=f"ยาสมมติ {i} (สำหรับทดสอบระบบ)", unit="หน่วย")
                )
            db.flush()
            if not db.get(StockLot, uid(f"lot{i}")):
                db.add(
                    StockLot(
                        id=uid(f"lot{i}"),
                        medicine_id=uid(f"med{i}"),
                        lot_number=f"DEMO-{i}",
                        expires_on=now.date() + timedelta(days=90),
                        quantity=100,
                    )
                )
                db.flush()
                db.add(
                    StockMovement(
                        lot_id=uid(f"lot{i}"),
                        actor_id=uid("pharmacy"),
                        quantity=100,
                        reason="fictional demo receive",
                        created_at=now,
                    )
                )
        if not db.get(Prescription, uid("rx")):
            db.add(
                Prescription(
                    id=uid("rx"),
                    visit_id=uid("visit1"),
                    provider_id=uid("practitioner"),
                    patient_name="คนไข้สมมติ 1 — ข้อมูลสาธิต",
                    allergies="ยังไม่ทราบ (ข้อมูลสมมติ)",
                    items=[
                        {
                            "medicine_id": str(uid("med1")),
                            "name": "ยาสมมติ 1 (สำหรับทดสอบระบบ)",
                            "unit": "หน่วย",
                            "quantity": 5,
                            "instructions": "ข้อความทดสอบ ไม่ใช้รักษาจริง",
                        }
                    ],
                    created_at=now,
                    status="prescribed",
                )
            )
        db.commit()
    print("Fictional demo seeded; existing records preserved. No real patient data.")


if __name__ == "__main__":
    main()
