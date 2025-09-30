from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, APIRouter
from fastapi.responses import ORJSONResponse

from app.api.v1.routes import auth
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import import_models

import_models()  # Importo i modelli perché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
    release=settings.SENTRY_RELEASE,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.SERVICE_NAME,
    default_response_class=ORJSONResponse,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,

)
if settings.ENVIRONMENT == "production":
    app = FastAPI(docs_url=None, redoc_url=None)  # nascondo la documentazione
else:
    app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# Routers
current_router = APIRouter()

current_router.include_router(
    prefix="/auth",
    tags=["auth"],
    router=auth.router,
)

app.include_router(current_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}
