import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select, update

from app.config import get_settings
from app.database import SessionLocal
from app.models.identity import LoginSession, PasswordReset, User
from app.services.identity import hash_password

logger = logging.getLogger(__name__)


def mail_configured():
    settings = get_settings()
    return bool(settings.resend_api_key and settings.reset_email_from and settings.reset_public_url)


def send_reset_email(email, token):
    settings = get_settings()
    link = f"{settings.reset_public_url}#reset={token}"
    # Token is placed in the URL fragment so web-server access logs do not receive it.
    with httpx.Client(timeout=10) as client:
        result = client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": "Bearer " + settings.resend_api_key.get_secret_value(),
                "Idempotency-Key": hashlib.sha256(token.encode()).hexdigest(),
            },
            json={
                "from": settings.reset_email_from,
                "to": [email],
                "subject": "ตั้งรหัสผ่านใหม่ — ธสัญญา คลินิก",
                "text": "ใช้ลิงก์นี้ภายใน 15 นาทีเพื่อตั้งรหัสผ่านใหม่ ใช้ได้ครั้งเดียว\n"
                + link
                + "\nหากไม่ได้ขอรีเซ็ต ไม่ต้องดำเนินการใด ๆ",
            },
        )
        result.raise_for_status()


def request_reset(email):
    # Executed after the generic response; never expose account existence or provider errors.
    try:
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.email == email, User.active.is_(True)).with_for_update()
            )
            if not user:
                return
            token = secrets.token_urlsafe(32)
            db.add(
                PasswordReset(
                    token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    user_id=user.id,
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
            )
            send_reset_email(email, token)
            db.commit()
    except Exception:
        logger.error("Password reset email delivery failed; no credentials logged")


def reset_password(db, payload):
    digest = hashlib.sha256(payload.token.get_secret_value().encode()).hexdigest()
    reset = db.get(PasswordReset, digest)
    if not reset:
        raise HTTPException(400, "Reset link is invalid or expired")
    user = db.scalar(select(User).where(User.id == reset.user_id).with_for_update())
    reset = db.scalar(
        select(PasswordReset)
        .where(PasswordReset.token_hash == digest)
        .execution_options(populate_existing=True)
    )
    if not user.active or reset.used or reset.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(400, "Reset link is invalid or expired")
    user.password_hash = hash_password(payload.new_password.get_secret_value())
    db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id).values(used=True))
    db.execute(update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True))
    db.commit()
