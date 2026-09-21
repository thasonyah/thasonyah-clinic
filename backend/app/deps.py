from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_session
from app.services.identity import PERMISSIONS, authenticate, unauthorized

bearer = HTTPBearer(auto_error=False)


def public_access() -> None:
    """Explicit policy for endpoints that contain no private data."""


def current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_session),
):
    if credentials is None:
        raise unauthorized()
    return authenticate(db, credentials.credentials)


def require_permission(permission):
    def check(identity=Depends(current_identity)):
        user, _ = identity
        if permission not in PERMISSIONS.get(user.role, []):
            raise HTTPException(403, "Permission denied")
        return user

    return check


def require_roles(*roles):
    def check(identity=Depends(current_identity)):
        user, _ = identity
        if user.role not in roles:
            raise HTTPException(403, "Permission denied")
        return user

    return check
