from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.billing import CashCloseInput, CashCloseOutput
from app.services.billing import close_cash, daily_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily")
def daily(
    day: date | None = None,
    user=Depends(require_roles("finance", "manager")),
    db: Session = Depends(get_session),
):
    return daily_report(db, day)


@router.post("/daily/close", response_model=CashCloseOutput, status_code=201)
def close_daily_cash(
    payload: CashCloseInput,
    day: date,
    user=Depends(require_roles("finance")),
    db: Session = Depends(get_session),
):
    return close_cash(db, user, day, payload)
