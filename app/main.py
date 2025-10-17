from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
import sys
from fastapi import FastAPI, APIRouter
from fastapi.responses import ORJSONResponse

from app.api.v1.routes import auth, users
from app.api.v1.routes import auth
from app.api.v1.routes import school
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.base import import_models
from app.services import broker, users as users_service

import_models()  # Importo i modelli perché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
    release=settings.SENTRY_RELEASE,
)

logger = None


# RabbitMQ Broker

exchanges = {
    "users": users_service.update_from_rabbitMQ,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.SERVICE_NAME,
    default_response_class=ORJSONResponse,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Routers
current_router = APIRouter()

current_router.include_router(
    prefix="/auth",
    tags=["auth"],
    router=auth.router,
)

current_router.include_router(
    prefix="/users",
    tags=["users"],
    router=users.router,
)

current_router.include_router(
    prefix="/school",
    tags=["school"],
    router=school.router,
)

app.include_router(current_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}
