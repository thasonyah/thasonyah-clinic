import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_permission
from app.schemas.catalog import ServiceInput, ServiceOutput, ServiceUpdate
from app.services import catalog

router = APIRouter(prefix="/services", tags=["services"])


@router.get(
    "",
    response_model=list[ServiceOutput],
    dependencies=[Depends(require_permission("clinic.read"))],
)
def list_services(db: Session = Depends(get_session)):
    return catalog.list_services(db)


@router.post(
    "",
    response_model=ServiceOutput,
    status_code=201,
    dependencies=[Depends(require_permission("clinic.manage"))],
)
def create_service(payload: ServiceInput, db: Session = Depends(get_session)):
    return catalog.create_service(db, payload)


@router.patch(
    "/{item_id}",
    response_model=ServiceOutput,
    dependencies=[Depends(require_permission("clinic.manage"))],
)
def update_service(item_id: uuid.UUID, payload: ServiceUpdate, db: Session = Depends(get_session)):
    return catalog.update_service(db, item_id, payload)
