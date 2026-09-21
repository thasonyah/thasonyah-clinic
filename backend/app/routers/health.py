from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import public_access
from app.schemas.health import HealthResponse
from app.services.health import database_ready

router = APIRouter(dependencies=[Depends(public_access)])


@router.get("/healthz", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=HealthResponse)
def ready(response: Response, session: Session = Depends(get_session)) -> HealthResponse:
    is_ready = database_ready(session)
    response.status_code = 200 if is_ready else 503
    return HealthResponse(status="ready" if is_ready else "unavailable")
