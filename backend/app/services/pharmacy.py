from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.pharmacy import DispenseBatch, Medicine, Prescription, StockLot, StockMovement
from app.models.records import Patient, Visit
from app.schemas.pharmacy import PrescriptionOutput
from app.services.audit import record
from app.services.records import owned_visit


def medicines(db):
    return list(db.scalars(select(Medicine).order_by(Medicine.name).limit(1000)))


def create_medicine(db, user, payload):
    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    try:
        db.flush()
        record(db, user, "medicine.create", medicine.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Medicine exists") from None
    return medicine


def lots(db):
    return list(db.scalars(select(StockLot).order_by(StockLot.expires_on, StockLot.id).limit(1000)))


def receive(db, user, payload):
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine or not medicine.active:
        raise HTTPException(422, "Medicine unavailable")
    lot = StockLot(**payload.model_dump())
    db.add(lot)
    try:
        db.flush()
        db.add(
            StockMovement(
                lot_id=lot.id,
                actor_id=user.id,
                quantity=lot.quantity,
                reason="receive",
                created_at=datetime.now(timezone.utc),
            )
        )
        record(db, user, "stock.receive", lot.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Medicine lot already received") from None
    return lot


def prescriptions(db, user, limit, offset):
    statement = select(Prescription)
    if user.role == "practitioner":
        statement = statement.where(Prescription.provider_id == user.id)
    return [
        output(db, rx)
        for rx in db.scalars(
            statement.order_by(Prescription.created_at.desc()).limit(limit).offset(offset)
        )
    ]


def prescribe(db, user, payload):
    visit = owned_visit(db, user, payload.visit_id)
    if not visit.signed_at:
        raise HTTPException(409, "Sign visit first")
    items = []
    for line in payload.items:
        med = db.get(Medicine, line.medicine_id)
        if not med or not med.active:
            raise HTTPException(422, "Medicine unavailable")
        items.append({**line.model_dump(mode="json"), "name": med.name, "unit": med.unit})
    patient = db.get(Patient, visit.patient_id)
    prescription = Prescription(
        visit_id=visit.id,
        provider_id=user.id,
        patient_name=patient.name,
        allergies=patient.allergies,
        items=items,
        created_at=datetime.now(timezone.utc),
    )
    db.add(prescription)
    try:
        db.flush()
        record(db, user, "prescription.create", prescription.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Visit already prescribed") from None
    return output(db, prescription)


def fulfilled(db, rx):
    delivered = {}
    allocations = []
    for movement, lot in db.execute(
        select(StockMovement, StockLot)
        .join(StockLot)
        .where(StockMovement.prescription_id == rx.id, StockMovement.quantity < 0)
        .order_by(StockMovement.created_at, StockMovement.id)
    ):
        key = str(lot.medicine_id)
        delivered[key] = delivered.get(key, 0) - movement.quantity
        allocations.append(
            {
                "medicine_id": key,
                "lot_number": lot.lot_number,
                "quantity": -movement.quantity,
                "expires_on": str(lot.expires_on),
                "created_at": movement.created_at.isoformat(),
                "actor_id": str(movement.actor_id),
            }
        )
    return delivered, allocations


def output(db, rx):
    result = PrescriptionOutput.model_validate(rx)
    delivered, result.allocations = fulfilled(db, rx)
    result.remaining = [
        {**line, "quantity": line["quantity"] - delivered.get(line["medicine_id"], 0)}
        for line in rx.items
        if line["quantity"] > delivered.get(line["medicine_id"], 0)
    ]
    visit = db.get(Visit, rx.visit_id)
    result.current_allergies = db.get(Patient, visit.patient_id).allergies
    return result


def dispense(db, user, prescription_id, payload):
    rx = db.scalar(select(Prescription).where(Prescription.id == prescription_id).with_for_update())
    if not rx:
        raise HTTPException(404, "Prescription not found")
    requested = None
    if payload.items is not None:
        requested = {}
        for line in payload.items:
            key = str(line.medicine_id)
            requested[key] = requested.get(key, 0) + line.quantity
    old = db.get(DispenseBatch, payload.request_id)
    if old:
        if old.prescription_id != rx.id or (requested is not None and requested != old.quantities):
            raise HTTPException(409, "Dispense request key changed")
        return output(db, rx)
    if rx.status not in ("prescribed", "partial"):
        raise HTTPException(409, "Prescription already dispensed or cancelled")
    delivered, _ = fulfilled(db, rx)
    pending = {
        line["medicine_id"]: line["quantity"] - delivered.get(line["medicine_id"], 0)
        for line in rx.items
    }
    needed = requested if requested is not None else {k: v for k, v in pending.items() if v > 0}
    if not needed or any(q > pending.get(k, 0) for k, q in needed.items()):
        raise HTTPException(422, "Quantity exceeds remaining prescription")
    now = datetime.now(timezone.utc)
    batch = DispenseBatch(
        id=payload.request_id,
        prescription_id=rx.id,
        quantities=needed,
        actor_id=user.id,
        created_at=now,
    )
    db.add(batch)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dispense request key reused") from None
    today = datetime.now(ZoneInfo("Asia/Bangkok")).date()
    for medicine_id in sorted(needed):
        remaining = needed[medicine_id]
        available = list(
            db.scalars(
                select(StockLot)
                .where(
                    StockLot.medicine_id == medicine_id,
                    StockLot.expires_on >= today,
                    StockLot.quantity > 0,
                )
                .order_by(StockLot.expires_on, StockLot.id)
                .with_for_update()
            )
        )
        for lot in available:
            take = min(lot.quantity, remaining)
            changed = db.execute(
                update(StockLot)
                .where(StockLot.id == lot.id, StockLot.quantity >= take)
                .values(quantity=StockLot.quantity - take)
            )
            if changed.rowcount != 1:
                db.rollback()
                raise HTTPException(409, "Stock changed; retry")
            db.add(
                StockMovement(
                    lot_id=lot.id,
                    prescription_id=rx.id,
                    batch_id=batch.id,
                    actor_id=user.id,
                    quantity=-take,
                    reason="dispense",
                    created_at=now,
                )
            )
            remaining -= take
            if remaining == 0:
                break
        if remaining:
            db.rollback()
            raise HTTPException(409, "Insufficient unexpired stock; nothing dispensed")
    rx.status = (
        "partial" if any(q - needed.get(k, 0) > 0 for k, q in pending.items()) else "dispensed"
    )
    rx.dispense_request = payload.request_id
    rx.dispensed_at = now
    record(db, user, "prescription.dispense", rx.id)
    db.commit()
    return output(db, rx)


def cancel(db, user, prescription_id):
    rx = db.scalar(
        select(Prescription)
        .where(Prescription.id == prescription_id, Prescription.provider_id == user.id)
        .with_for_update()
    )
    if not rx:
        raise HTTPException(404, "Prescription not found")
    if rx.status not in ("prescribed", "partial"):
        raise HTTPException(409, "Cannot cancel after dispensing")
    rx.status = "cancelled"
    record(db, user, "prescription.cancel", rx.id)
    db.commit()
    return output(db, rx)


def adjust_stock(db, user, lot_id, payload):
    lot = db.scalar(select(StockLot).where(StockLot.id == lot_id).with_for_update())
    if not lot:
        raise HTTPException(404, "Lot not found")
    reason = payload.kind + ": " + payload.reason
    old = db.scalar(select(StockMovement).where(StockMovement.request_id == payload.request_id))
    if old:
        if (
            old.lot_id != lot_id
            or old.balance != payload.quantity
            or old.reason != reason
            or old.balance - old.quantity != payload.expected_quantity
        ):
            raise HTTPException(409, "Adjustment request key changed")
        return lot
    if lot.quantity != payload.expected_quantity:
        raise HTTPException(409, "Stock changed; reload the lot before counting again")
    if (payload.kind == "damage" and payload.quantity > lot.quantity) or (
        payload.kind == "return" and payload.quantity < lot.quantity
    ):
        raise HTTPException(422, "Invalid quantity for this movement type")
    delta = payload.quantity - lot.quantity
    changed = db.execute(
        update(StockLot)
        .where(StockLot.id == lot_id, StockLot.quantity == payload.expected_quantity)
        .values(quantity=payload.quantity)
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Stock changed")
    db.add(
        StockMovement(
            lot_id=lot_id,
            actor_id=user.id,
            quantity=delta,
            balance=payload.quantity,
            reason=reason,
            request_id=payload.request_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    record(db, user, "stock." + payload.kind, lot_id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Adjustment request key reused") from None
    return db.get(StockLot, lot_id)


def stock_history(db, lot_id):
    if not db.get(StockLot, lot_id):
        raise HTTPException(404, "Lot not found")
    return list(
        db.scalars(
            select(StockMovement)
            .where(StockMovement.lot_id == lot_id)
            .order_by(StockMovement.created_at.desc(), StockMovement.id)
            .limit(1000)
        )
    )
