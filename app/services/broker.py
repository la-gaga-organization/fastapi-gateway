from __future__ import annotations

import pika
import asyncio
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.session import SessionLocal
from app.services.user_service import upsert_user_from_event

logger = get_logger(__name__)

class BrokerSingleton:
    """Singleton per la gestione della connessione a RabbitMQ e delle operazioni di publish/subscribe.
    """
    _instance = None
    _connection = None
    _exchanges = {}

    def __new__(cls):
        if cls._instance is None:
            setup_logging()
            logger.info("Starting broker consumer...")
            cls._instance = super().__new__(cls)
            cls._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
            )
            if cls._connection.is_open:
                logger.info("Connected to RabbitMQ")
            else:
                logger.error("Failed to connect to RabbitMQ")
                raise ConnectionError("Failed to connect to RabbitMQ")
            cls._exchanges = {}
        return cls._instance

    @property
    def connection(self):
        """Restituisce la connessione RabbitMQ.

        Returns:
            pika.BlockingConnection: Connessione RabbitMQ.
        """
        return self._connection

    def subscribe(self, exchange_name: str, callback, ex_type: str = "fanout", routing_key: str = ""):
        """Iscrive a un exchange RabbitMQ e inizia a consumare i messaggi.

        Args:
            exchange_name (str): Nome dell'exchange.
            callback (function): Funzione di callback per gestire i messaggi ricevuti.
            ex_type (str, optional): Tipo di exchange. Defaults to "fanout".
            routing_key (str, optional): Chiave di routing. Defaults to "".
        """
        channel = self.declare(exchange_name, ex_type)
        queue_result = channel.queue_declare(queue=f'queue_{exchange_name}', exclusive=True)
        queue_name = queue_result.method.queue
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        logger.info(f"Subscribed to exchange {exchange_name} with queue {queue_name}")
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    def unsubscribe(self, exchange_name: str):
        """Annulla l'iscrizione a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
        """
        if exchange_name in self._exchanges:
            channel = self._exchanges[exchange_name]
            channel.stop_consuming()
            del self._exchanges[exchange_name]
            logger.info(f"Unsubscribed from exchange {exchange_name}")

    def declare(self, exchange_name: str, t: str = "fanout"):
        """Dichiara un exchange RabbitMQ se non esiste già.

        Args:
            exchange_name (str): Nome dell'exchange.
            t (str, optional): Tipo di exchange. Defaults to "fanout".
        Returns:
            pika.channel.Channel: Canale collegato all'exchange.
        """
        if exchange_name not in self._exchanges:
            channel = self._connection.channel()
            channel.exchange_declare(exchange=exchange_name, exchange_type=t)
            self._exchanges[exchange_name] = channel
            logger.info(f"Declared exchange {exchange_name}")
        return self._exchanges[exchange_name]

    def send(self, exchange_name: str, type: str, data: dict):
        """Manda un messaggio a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
            type (str): Tipo di evento.
            data (dict): Dati dell'evento.
        """
        channel = self.declare(exchange_name)
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='',
            body={
                "type": type,
                "data": data
            }
        )
        logger.info(f"Sent message to exchange {exchange_name}. Type: {type}")