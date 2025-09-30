from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import import_models

import_models()  # Importo i modelli perché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.GATEWAY_SENTRY_DSN,
    send_default_pii=True,
    release=settings.GATEWAY_SENTRY_RELEASE,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.GATEWAY_SERVICE_NAME,
    default_response_class=ORJSONResponse,
    version=settings.GATEWAY_SERVICE_VERSION,
    lifespan=lifespan,

)
if settings.GATEWAY_ENVIRONMENT == "production":
    app = FastAPI(docs_url=None, redoc_url=None)  # nascondo la documentazione
else:
    app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# Routers


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.GATEWAY_SERVICE_NAME}
