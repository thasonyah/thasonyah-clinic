from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import Numeric, func, literal, select, union_all
from sqlalchemy.exc import IntegrityError

from app.models.billing import CashClose, Invoice, PaymentReceipt, PaymentRefund
from app.models.catalog import ClinicService
from app.models.records import Patient
from app.services.audit import record
from app.services.records import owned_visit


def list_invoices(db, user, limit, offset):
    statement = select(Invoice)
    if user.role == "practitioner":
        statement = statement.where(Invoice.provider_id == user.id)
    return list(db.scalars(statement.order_by(Invoice.number.desc()).limit(limit).offset(offset)))


def create_invoice(db, user, payload):
    visit = owned_visit(db, user, payload.visit_id)
    if not visit.signed_at:
        raise HTTPException(409, "Sign visit before billing")
    if db.scalar(select(Invoice.id).where(Invoice.visit_id == visit.id)):
        raise HTTPException(409, "Visit already invoiced")
    items = []
    total = Decimal("0.00")
    for line in payload.items:
        service = db.get(ClinicService, line.service_id)
        if not service or not service.active:
            raise HTTPException(422, "Service unavailable")
        amount = service.price * line.quantity
        total += amount
        items.append(
            {
                "service_id": str(service.id),
                "name": service.name,
                "price": str(service.price),
                "quantity": line.quantity,
                "amount": str(amount),
            }
        )
    if total > Decimal("9999999999.99"):
        raise HTTPException(422, "Total too large")
    invoice = Invoice(
        visit_id=visit.id,
        provider_id=user.id,
        patient_name=db.get(Patient, visit.patient_id).name,
        items=items,
        total=total,
        created_at=datetime.now(timezone.utc),
    )
    db.add(invoice)
    try:
        db.flush()
        record(db, user, "invoice.create", invoice.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Visit already invoiced") from None
    return invoice


def locked(db, invoice_id):
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id).with_for_update())
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice


def commit_money(db, user, invoice, action):
    record(db, user, action, invoice.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Request key already used") from None
    return invoice


def refresh_state(db, invoice):
    db.flush()
    db.expire(invoice, ["payments", "refunds"])
    paid, refunded = invoice.paid_total, invoice.refunded_total
    if refunded and refunded == paid:
        invoice.status = "refunded"
    elif refunded:
        invoice.status = "partially_refunded"
    elif paid >= invoice.total:
        invoice.status = "paid"
    elif paid:
        invoice.status = "partial"
    else:
        invoice.status = "outstanding"


def pay(db, user, invoice_id, payload):
    invoice = locked(db, invoice_id)
    old = db.scalar(select(PaymentReceipt).where(PaymentReceipt.request_id == payload.request_id))
    if old:
        if (
            old.invoice_id != invoice_id
            or old.amount != payload.amount
            or old.method != payload.method
        ):
            raise HTTPException(409, "Request key changed")
        return invoice
    if payload.amount > invoice.due_total:
        raise HTTPException(409, "Payment exceeds outstanding balance")
    now = datetime.now(timezone.utc)
    db.add(
        PaymentReceipt(
            invoice_id=invoice.id,
            request_id=payload.request_id,
            amount=payload.amount,
            method=payload.method,
            actor_id=user.id,
            created_at=now,
        )
    )
    invoice.paid_at = now
    methods = {p.method for p in invoice.payments} | {payload.method}
    invoice.payment_method = payload.method if len(methods) == 1 else "mixed"
    try:
        refresh_state(db, invoice)
        return commit_money(db, user, invoice, "invoice.pay")
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Payment request already used") from None


def refund(db, user, invoice_id, payload):
    invoice = locked(db, invoice_id)
    old = db.scalar(select(PaymentRefund).where(PaymentRefund.request_id == payload.request_id))
    if old:
        if (
            old.invoice_id != invoice_id
            or old.reason != payload.reason
            or (payload.amount is not None and old.amount != payload.amount)
            or (payload.method is not None and old.method != payload.method)
        ):
            raise HTTPException(409, "Request key changed")
        return invoice
    methods = {p.method for p in invoice.payments}
    method = payload.method or (next(iter(methods)) if len(methods) == 1 else None)
    if not method:
        raise HTTPException(422, "Choose a refund method")
    available = sum((p.amount for p in invoice.payments if p.method == method), Decimal("0.00"))
    available -= sum((p.amount for p in invoice.refunds if p.method == method), Decimal("0.00"))
    amount = payload.amount if payload.amount is not None else available
    if amount <= 0 or amount > available:
        raise HTTPException(409, "Refund exceeds the refundable balance of this method")
    now = datetime.now(timezone.utc)
    db.add(
        PaymentRefund(
            invoice_id=invoice.id,
            request_id=payload.request_id,
            amount=amount,
            method=method,
            actor_id=user.id,
            reason=payload.reason,
            created_at=now,
        )
    )
    invoice.refund_reason = payload.reason
    invoice.refunded_at = now
    try:
        refresh_state(db, invoice)
        return commit_money(db, user, invoice, "invoice.refund")
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Refund request already used") from None


def daily_report(db, day):
    zone = ZoneInfo("Asia/Bangkok")
    day = day or datetime.now(zone).date()
    start = datetime.combine(day, time.min, tzinfo=zone)
    end = start + timedelta(days=1)
    zero = literal(Decimal("0.00"), Numeric(12, 2))
    entries = union_all(
        select(
            PaymentReceipt.method.label("method"),
            PaymentReceipt.amount.label("receipts"),
            zero.label("refunds"),
        ).where(PaymentReceipt.created_at >= start, PaymentReceipt.created_at < end),
        select(
            PaymentRefund.method.label("method"),
            zero.label("receipts"),
            PaymentRefund.amount.label("refunds"),
        ).where(PaymentRefund.created_at >= start, PaymentRefund.created_at < end),
    ).subquery()
    channels = {}
    receipts = refunds = Decimal("0.00")
    for method, received, returned in db.execute(
        select(
            entries.c.method, func.sum(entries.c.receipts), func.sum(entries.c.refunds)
        ).group_by(entries.c.method)
    ):
        receipts += received
        refunds += returned
        channels[method] = {
            "receipts": str(received),
            "refunds": str(returned),
            "net": str(received - returned),
        }
    close = db.scalar(select(CashClose).where(CashClose.day == day))
    return {
        "day": str(day),
        "receipts": str(receipts),
        "refunds": str(refunds),
        "net": str(receipts - refunds),
        "channels": channels,
        "cash_close": {
            "id": str(close.id),
            "day": str(close.day),
            "actor_id": str(close.actor_id) if close.actor_id else None,
            "expected_cash": str(close.expected_cash),
            "counted_cash": str(close.counted_cash),
            "difference": str(close.difference),
            "note": close.note,
            "channels": close.channels,
            "created_at": close.created_at.isoformat(),
        }
        if close
        else None,
    }


def close_cash(db, user, day, payload):
    report = daily_report(db, day)
    expected = Decimal(report["channels"].get("cash", {}).get("net", "0.00"))
    close = CashClose(
        day=day,
        actor_id=user.id,
        expected_cash=expected,
        counted_cash=payload.counted_cash,
        difference=payload.counted_cash - expected,
        note=payload.note,
        channels=report["channels"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(close)
    try:
        db.flush()
        record(db, user, "cash_close.create", close.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Cash already closed for this day") from None
    return close
