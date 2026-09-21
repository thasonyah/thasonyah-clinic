import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.models.identity import LoginSession, PasswordReset, User
from app.schemas.identity import UserOutput
from app.services.audit import record

passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
PERMISSIONS = {
    "admin": ["users.manage", "clinic.read", "clinic.manage"],
    "manager": ["clinic.read", "reports.read"],
    "practitioner": ["clinic.read", "clinical.read", "clinical.write", "clinical.sign"],
    "reception": ["clinic.read", "patients.read", "patients.create", "scheduling.write"],
    "finance": ["clinic.read", "billing.read", "billing.write"],
    "pharmacy": ["clinic.read", "dispensing.read", "dispensing.write"],
}


def hash_password(value):
    return passwords.hash(value)


DUMMY_HASH = hash_password(secrets.token_urlsafe(24))


def unauthorized():
    return HTTPException(
        401, "Invalid credentials or session", headers={"WWW-Authenticate": "Bearer"}
    )


def login(db, payload):
    user = db.scalar(select(User).where(User.email == payload.email).with_for_update())
    valid = passwords.verify(
        payload.password.get_secret_value(), user.password_hash if user else DUMMY_HASH
    )
    if not valid or not user or not user.active:
        raise unauthorized()
    settings = get_settings()
    now = datetime.now(timezone.utc)
    session = LoginSession(
        user_id=user.id, expires_at=now + timedelta(minutes=settings.access_token_minutes)
    )
    db.add(session)
    db.flush()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "sid": str(session.id),
            "iat": now,
            "exp": session.expires_at,
            "iss": "clinic-api",
            "aud": "clinic-web",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    db.commit()
    return {
        "access_token": token,
        "expires_in": settings.access_token_minutes * 60,
        "user_summary": UserOutput.model_validate(user),
    }


def authenticate(db, token):
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience="clinic-web",
            issuer="clinic-api",
            options={"require_exp": True, "require_sub": True, "require_iat": True},
        )
        sid, uid = uuid.UUID(claims["sid"]), uuid.UUID(claims["sub"])
    except (JWTError, ValueError, KeyError, TypeError):
        raise unauthorized() from None
    session = db.get(LoginSession, sid)
    user = db.get(User, uid)
    if (
        not session
        or session.user_id != uid
        or session.revoked
        or session.expires_at <= datetime.now(timezone.utc)
        or not user
        or not user.active
    ):
        raise unauthorized()
    return user, session


def logout(db, session):
    session.revoked = True
    db.commit()


def change_password(db, user, payload):
    user = db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not passwords.verify(payload.current_password.get_secret_value(), user.password_hash):
        raise unauthorized()
    user.password_hash = hash_password(payload.new_password.get_secret_value())
    db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id).values(used=True))
    db.execute(update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True))
    db.commit()


def create_user(db, payload):
    user = User(
        email=payload.email,
        role=payload.role,
        password_hash=hash_password(payload.password.get_secret_value()),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account already exists") from None
    return user


def list_users(db, limit, offset):
    return list(db.scalars(select(User).order_by(User.id).limit(limit).offset(offset)))


def set_user_status(db, actor, user_id, active):
    # Serialise status changes across administrators, including the last-admin check.
    admins = list(
        db.scalars(select(User).where(User.role == "admin").order_by(User.id).with_for_update())
    )
    target = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not target:
        raise HTTPException(404, "Account not found")
    if not active and (
        target.id == actor.id
        or (target.role == "admin" and target.active and sum(u.active for u in admins) <= 1)
    ):
        raise HTTPException(409, "Cannot disable yourself or the last administrator")
    target.active = active
    if not active:
        db.execute(
            update(LoginSession).where(LoginSession.user_id == target.id).values(revoked=True)
        )
        db.execute(
            update(PasswordReset).where(PasswordReset.user_id == target.id).values(used=True)
        )
    record(db, actor, "user.status", target.id)
    db.commit()
    return target
