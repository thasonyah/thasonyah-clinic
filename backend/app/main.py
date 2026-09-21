from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.routers.appointments import router as appointments_router
from app.routers.audit import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.health import router
from app.routers.invoices import router as invoices_router
from app.routers.lots import router as lots_router
from app.routers.medicines import router as medicines_router
from app.routers.patients import router as patients_router
from app.routers.prescriptions import router as prescriptions_router
from app.routers.reports import router as reports_router
from app.routers.resources import router as resources_router
from app.routers.users import router as users_router
from app.routers.visits import router as visits_router
from app.services.bootstrap import ensure_bootstrap_admin

app = FastAPI(title="Thai Traditional Medicine Clinic API")


@app.on_event("startup")
def bootstrap_admin_account():
    ensure_bootstrap_admin()

app.state.limiter = Limiter(key_func=get_remote_address)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
app.include_router(router, prefix="/api/v1")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo submitted passwords or other private request values in errors.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {"loc": list(error["loc"]), "type": error["type"], "msg": "Invalid value"}
                for error in exc.errors()
            ]
        },
    )


app.include_router(catalog_router, prefix="/api/v1")


app.include_router(patients_router, prefix="/api/v1")
app.include_router(visits_router, prefix="/api/v1")

app.include_router(audit_router, prefix="/api/v1")

app.include_router(appointments_router, prefix="/api/v1")
app.include_router(resources_router, prefix="/api/v1")

app.include_router(invoices_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")

app.include_router(medicines_router, prefix="/api/v1")
app.include_router(lots_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
