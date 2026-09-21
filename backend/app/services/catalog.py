from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.catalog import ClinicService


def list_services(db):
    return list(db.scalars(select(ClinicService).order_by(ClinicService.name)))


def create_service(db, payload):
    item = ClinicService(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Service name already exists") from None
    return item


def update_service(db, item_id, payload):
    values = payload.model_dump(exclude={"expected_version"})
    try:
        result = db.execute(
            update(ClinicService)
            .where(ClinicService.id == item_id, ClinicService.version == payload.expected_version)
            .values(**values, version=ClinicService.version + 1)
        )
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Service changed or no longer exists; reload and retry")
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Service name already exists") from None
    return db.get(ClinicService, item_id)
