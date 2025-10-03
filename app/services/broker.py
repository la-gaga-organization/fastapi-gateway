from __future__ import annotations

import json
import asyncio
import aio_pika

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)

class AsyncBrokerSingleton:
    """Singleton asincrono per la gestione della connessione a RabbitMQ e delle operazioni di publish/subscribe."""
    _instance = None
    _service_name = ""

    def __new__(cls, service_name: str = settings.SERVICE_NAME):
        if cls._instance is None:
            setup_logging()
            logger.info("Starting async broker consumer...")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, service_name: str = settings.SERVICE_NAME):
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.queues = {}
        self.tasks = {}

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS
        )
        self.channel = await self.connection.channel()
        logger.info("Connected to RabbitMQ (aio-pika)")

    async def subscribe(self, exchange_name, callback, ex_type="direct", routing_key=""):
        exchange = await self.channel.declare_exchange(exchange_name, ex_type)
        queue = await self.channel.declare_queue(
            f"{self.service_name}.{exchange_name}.{routing_key if routing_key else 'all'}",
            durable=True
        )
        await queue.bind(exchange, routing_key=routing_key)
        task = asyncio.create_task(queue.consume(callback))
        self.queues[(exchange_name, routing_key)] = queue
        self.tasks[(exchange_name, routing_key)] = task
        logger.info(f"Subscribed to exchange {exchange_name} with routing key '{routing_key}' (aio-pika)")

    async def unsubscribe(self, exchange_name, routing_key=""):
        key = (exchange_name, routing_key)
        if key in self.tasks:
            self.tasks[key].cancel()
            await asyncio.sleep(0)  # consenti la cancellazione
            del self.tasks[key]
        if key in self.queues:
            await self.queues[key].unbind()
            await self.queues[key].delete()
            del self.queues[key]
        logger.info(f"Unsubscribed from exchange {exchange_name} with routing key '{routing_key}' (aio-pika)")

    async def publish_message(self, exchange_name, event_type, data, routing_key=""):
        exchange = await self.channel.declare_exchange(exchange_name, "direct")
        message = aio_pika.Message(
            body=json.dumps({"type": event_type, "data": data}).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Sent message to exchange {exchange_name}. Type: {event_type} (aio-pika)")

    async def close(self):
        for key in list(self.tasks.keys()):
            await self.unsubscribe(*key)
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Closed all RabbitMQ consumer tasks (aio-pika)")

def declare_services_exchanges(exchanges: dict):
    """Dichiara e sottoscrive agli exchange RabbitMQ specificati nel dizionario exchanges (asincrono)."""
    async def runner():
        broker_instance = AsyncBrokerSingleton()
        await broker_instance.connect()
        for exchange, callback in exchanges.items():
            await broker_instance.subscribe(exchange, callback)
    asyncio.run(runner())
