"""Run python -m scripts.bootstrap_admin; credentials come only from config/env."""

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.identity import User
from app.schemas.identity import CreateUser
from app.services.identity import create_user


def main():
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        raise SystemExit("Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD")
    payload = CreateUser(
        email=settings.bootstrap_admin_email,
        password=settings.bootstrap_admin_password,
        role="admin",
    )
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.role == "admin", User.active.is_(True))):
            raise SystemExit("An active administrator already exists; no changes made")
        create_user(db, payload)
    print("Administrator created. Remove bootstrap credentials from the environment.")


if __name__ == "__main__":
    main()
