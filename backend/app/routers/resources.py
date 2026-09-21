import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_roles
from app.schemas.identity import UserStatus
from app.schemas.scheduling import ResourceInput, ResourceOutput
from app.services import scheduling

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOutput])
def listing(
    user=Depends(require_roles("admin", "reception", "practitioner")),
    db: Session = Depends(get_session),
):
    return scheduling.list_resources(db)


@router.post("", response_model=ResourceOutput, status_code=201)
def create(
    payload: ResourceInput, user=Depends(require_roles("admin")), db: Session = Depends(get_session)
):
    return scheduling.create_resource(db, user, payload)


@router.patch("/{resource_id}/status", response_model=ResourceOutput)
def status(
    resource_id: uuid.UUID,
    payload: UserStatus,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_session),
):
    return scheduling.resource_status(db, user, resource_id, payload.active)
