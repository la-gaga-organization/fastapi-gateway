from __future__ import annotations

import json

import pika

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


class BrokerSingleton:
    """Singleton per la gestione della connessione a RabbitMQ e delle operazioni di publish/subscribe.
    """
    _instance = None
    _connection = None
    _exchanges = {}
    _service_name = ""

    def __new__(cls):
        if cls._instance is None:
            setup_logging()
            logger.info("Starting broker consumer...")
            cls._instance = super().__new__(cls)
            credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
            cls._connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    credentials=credentials
                )
            )
            if cls._connection.is_open:
                logger.info("Connected to RabbitMQ")
            else:
                logger.error("Failed to connect to RabbitMQ")
                raise ConnectionError("Failed to connect to RabbitMQ")
            cls._exchanges = {}
        return cls._instance

    def __init__(self, service_name: str = settings.SERVICE_NAME):
        self.service_name = service_name

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
        queue_result = channel.queue_declare(
            queue=f'{self.service_name}.{exchange_name}.{routing_key if routing_key else "all"}',
            exclusive=False,  # non elimina la coda alla disconnessione
            durable=True,  # la coda sopravvive al riavvio del server RabbitMQ, salvando i messaggi su disco
            auto_delete=True  # la coda non viene eliminata automaticamente quando non ci sono consumatori
        )
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
            channel.exchange_delete(exchange=exchange_name)
            #channel.stop_consuming()
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

    def publish_message(self, exchange_name: str, type: str, data: dict):
        """
        Manda un messaggio a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
            type (str): Tipo di evento.
            data (dict): Dati dell'evento.
        """
        channel = self.declare(exchange_name)

        message = {
            "type": type,
            "data": data
        }

        channel.basic_publish(
            exchange=exchange_name,
            routing_key='',
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2  # rendo il messaggio persistente
            )
        )

        logger.info(f"Sent message to exchange {exchange_name}. Type: {type}")
