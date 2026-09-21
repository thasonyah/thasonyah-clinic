from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import current_identity, public_access
from app.schemas.identity import (
    ChangePassword,
    LoginInput,
    LoginOutput,
    MeOutput,
)
from app.schemas.password_reset import ForgotPassword, ResetPassword
from app.services import identity as service
from app.services import password_reset

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=LoginOutput, dependencies=[Depends(public_access)])
@limiter.limit("10/minute")
def login(
    request: Request, payload: LoginInput, response: Response, db: Session = Depends(get_session)
):
    response.headers["Cache-Control"] = "no-store"
    return service.login(db, payload)


@router.get("/me", response_model=MeOutput)
def me(identity=Depends(current_identity)):
    user, _ = identity
    return MeOutput.model_validate(user).model_copy(
        update={"permissions": service.PERMISSIONS.get(user.role, [])}
    )


@router.post("/logout", status_code=204)
def logout(identity=Depends(current_identity), db: Session = Depends(get_session)):
    service.logout(db, identity[1])


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePassword, identity=Depends(current_identity), db: Session = Depends(get_session)
):
    service.change_password(db, identity[0], payload)


@router.post("/forgot-password", status_code=202, dependencies=[Depends(public_access)])
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPassword, tasks: BackgroundTasks):
    if not password_reset.mail_configured():
        raise HTTPException(503, "Password recovery email is not configured; contact administrator")
    tasks.add_task(password_reset.request_reset, payload.email)
    return {"message": "If an active account matches, a reset link will be sent"}


@router.post("/reset-password", status_code=204, dependencies=[Depends(public_access)])
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPassword, db: Session = Depends(get_session)):
    password_reset.reset_password(db, payload)
