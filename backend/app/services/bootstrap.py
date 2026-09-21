from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.identity import User
from app.services.identity import hash_password


def ensure_bootstrap_admin() -> bool:
    """Create the first active admin from env vars when no active admin exists.

    Returns True when a new admin was created. This is intentionally conservative:
    existing active admins are never modified, and partial bootstrap configuration is
    ignored so normal deploys do not fail because the optional password was omitted.
    """
    settings = get_settings()
    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password
    if not email or not password:
        return False

    normalized_email = email.strip().lower()
    if not normalized_email:
        return False

    with SessionLocal() as db:
        active_admin = db.scalar(select(User.id).where(User.role == "admin", User.active.is_(True)))
        if active_admin:
            return False

        existing = db.scalar(select(User).where(User.email == normalized_email).with_for_update())
        if existing:
            existing.role = "admin"
            existing.active = True
            existing.password_hash = hash_password(password.get_secret_value())
        else:
            db.add(
                User(
                    email=normalized_email,
                    role="admin",
                    password_hash=hash_password(password.get_secret_value()),
                    active=True,
                )
            )
        db.commit()
        return True
