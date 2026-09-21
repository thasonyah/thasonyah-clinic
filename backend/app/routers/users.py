import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import require_permission
from app.schemas.identity import CreateUser, UserOutput, UserStatus
from app.services import identity as service

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_permission("users.manage"))]
)


@router.get("", response_model=list[UserOutput])
def list_users(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    return service.list_users(db, limit, offset)


@router.post("", response_model=UserOutput, status_code=201)
def create_user(payload: CreateUser, db: Session = Depends(get_session)):
    return service.create_user(db, payload)


@router.patch("/{user_id}/status", response_model=UserOutput)
def status(
    user_id: uuid.UUID,
    payload: UserStatus,
    actor=Depends(require_permission("users.manage")),
    db: Session = Depends(get_session),
):
    return service.set_user_status(db, actor, user_id, payload.active)
