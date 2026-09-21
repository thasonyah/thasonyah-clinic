from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.pharmacy import MedicineInput, MedicineOutput
from app.services import pharmacy

router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineOutput])
def listing(
    user=Depends(require_roles("practitioner", "pharmacy")), db: Session = Depends(get_session)
):
    return pharmacy.medicines(db)


@router.post("", response_model=MedicineOutput, status_code=201)
def create(
    payload: MedicineInput,
    user=Depends(require_roles("pharmacy")),
    db: Session = Depends(get_session),
):
    return pharmacy.create_medicine(db, user, payload)
