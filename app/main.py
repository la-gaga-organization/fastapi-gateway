from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, APIRouter
from fastapi.responses import ORJSONResponse

from app.api.v1.routes import auth, users
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.base import import_models
from app.services import broker

import_models()  # Importo i modelli perché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
    release=settings.SENTRY_RELEASE,
)

logger = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.SERVICE_NAME}...")
    yield
    broker_instance = broker.BrokerSingleton()
    if broker_instance:
        broker_instance.close()
        logger.info(f"Broker {broker_instance} closed")

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

current_router.include_router(
    prefix="/users",
    tags=["users"],
    router=users.router,
)

app.include_router(current_router, prefix="/api/v1")

# RabbitMQ Broker
async def callback(message):
    async with message.process():
        print(f"Received message from exchange '{message.exchange}' with routing key '{message.routing_key}': {message.body.decode()}")

exchanges = {
    "users": callback,
    "banana": callback
}

broker.declare_services_exchanges(exchanges)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}