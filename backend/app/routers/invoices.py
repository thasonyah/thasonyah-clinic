import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.billing import InvoiceInput, InvoiceOutput, PaymentInput, RefundInput
from app.services import billing

router = APIRouter(prefix="/invoices", tags=["invoices"])
finance = require_roles("finance")


@router.get("", response_model=list[InvoiceOutput])
def listing(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(require_roles("finance", "practitioner")),
    db: Session = Depends(get_session),
):
    return billing.list_invoices(db, user, limit, offset)


@router.post("", response_model=InvoiceOutput, status_code=201)
def create(
    payload: InvoiceInput,
    user=Depends(require_roles("practitioner")),
    db: Session = Depends(get_session),
):
    return billing.create_invoice(db, user, payload)


@router.post("/{invoice_id}/payment", response_model=InvoiceOutput)
def payment(
    invoice_id: uuid.UUID,
    payload: PaymentInput,
    user=Depends(finance),
    db: Session = Depends(get_session),
):
    return billing.pay(db, user, invoice_id, payload)


@router.post("/{invoice_id}/refund", response_model=InvoiceOutput)
def refund(
    invoice_id: uuid.UUID,
    payload: RefundInput,
    user=Depends(finance),
    db: Session = Depends(get_session),
):
    return billing.refund(db, user, invoice_id, payload)
