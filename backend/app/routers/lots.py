import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.pharmacy import LotInput, LotOutput, MovementOutput, StockAdjustment
from app.services import pharmacy

router = APIRouter(prefix="/lots", tags=["lots"])


@router.get("", response_model=list[LotOutput])
def listing(user=Depends(require_roles("pharmacy")), db: Session = Depends(get_session)):
    return pharmacy.lots(db)


@router.post("", response_model=LotOutput, status_code=201)
def receive(
    payload: LotInput, user=Depends(require_roles("pharmacy")), db: Session = Depends(get_session)
):
    return pharmacy.receive(db, user, payload)


@router.post("/{lot_id}/adjust", response_model=LotOutput)
def adjust(
    lot_id: uuid.UUID,
    payload: StockAdjustment,
    user=Depends(require_roles("pharmacy")),
    db: Session = Depends(get_session),
):
    return pharmacy.adjust_stock(db, user, lot_id, payload)


@router.get("/{lot_id}/movements", response_model=list[MovementOutput])
def history(
    lot_id: uuid.UUID, user=Depends(require_roles("pharmacy")), db: Session = Depends(get_session)
):
    return pharmacy.stock_history(db, lot_id)
