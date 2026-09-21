from sqlalchemy import select

from app.models.audit import AuditEvent


def record(db, user, action, target):
    db.add(AuditEvent(actor_id=user.id, action=action, target_id=str(target)))


def recent(db, limit, offset):
    return list(
        db.scalars(
            select(AuditEvent)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id)
            .limit(limit)
            .offset(offset)
        )
    )
