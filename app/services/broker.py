from __future__ import annotations

import json
import threading

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
    _threads = {}
    _service_name = ""

    def __new__(cls):
        if cls._instance is None:
            setup_logging()
            logger.info("Starting broker consumer...")
            cls._instance = super().__new__(cls)
            credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
            try:
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
            except Exception as e:
                logger.exception(f"Error connecting to RabbitMQ: {str(e)}")
                return None

    def __init__(self, service_name: str = settings.SERVICE_NAME):
        self.service_name = service_name

    @property
    def connection(self):
        """Restituisce la connessione RabbitMQ.

        Returns:
            pika.BlockingConnection: Connessione RabbitMQ.
        """
        return self._connection

    def subscribe(self, exchange_name: str, callback, ex_type: str = "direct", routing_key: str = ""):
        """Iscrive a un exchange RabbitMQ e inizia a consumare i messaggi.

        Args:
            exchange_name (str): Nome dell'exchange.
            callback (function): Funzione di callback per gestire i messaggi ricevuti.
            ex_type (str, optional): Tipo di exchange. Defaults to "direct".
            routing_key (str, optional): Chiave di routing. Defaults to "". Lascia vuoto per ricevere tutti i messaggi.
        """
        channel = self.declare(exchange_name, ex_type)
        queue_result = channel.queue_declare(
            queue=f'{self.service_name}.{exchange_name}.{routing_key if routing_key else "all"}',
            exclusive=False,  # non elimina la coda alla disconnessione
            durable=True,  # la coda sopravvive al riavvio del server RabbitMQ, salvando i messaggi su disco
            auto_delete=False  # la coda non viene eliminata automaticamente quando non ci sono consumatori
        )
        queue_name = queue_result.method.queue
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        logger.info(f"Subscribed to exchange {exchange_name} with queue {queue_name}")
        def consume():
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            try:
                channel.start_consuming()
            except Exception as e:
                logger.info(f"Stopped consuming for exchange {exchange_name}: {e}")
        thread = threading.Thread(target=consume, daemon=True)
        thread.start()
        self._threads[exchange_name] = (thread, channel)
        logger.info(f"Started consuming in a separate thread for exchange {exchange_name}")

    def unsubscribe(self, exchange_name: str):
        """Annulla l'iscrizione a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
        """
        if exchange_name in self._threads:
            thread, channel = self._threads[exchange_name]
            try:
                channel.stop_consuming()
            except Exception as e:
                logger.error(f"Error stopping consumer for {exchange_name}: {e}")
            thread.join(timeout=2)
            del self._threads[exchange_name]
            logger.info(f"Stopped consumer thread for exchange {exchange_name}")

        if exchange_name in self._exchanges:
            channel = self._exchanges[exchange_name]
            channel.exchange_delete(exchange=exchange_name)
            del self._exchanges[exchange_name]
            logger.info(f"Unsubscribed from exchange {exchange_name}")

    def declare(self, exchange_name: str, t: str = "direct"):
        """Dichiara un exchange RabbitMQ se non esiste già.

        Args:
            exchange_name (str): Nome dell'exchange.
            t (str, optional): Tipo di exchange. Defaults to "direct".
        Returns:
            pika.channel.Channel: Canale collegato all'exchange.
        """
        if exchange_name not in self._exchanges:
            channel = self._connection.channel()
            channel.exchange_declare(exchange=exchange_name, exchange_type=t)
            self._exchanges[exchange_name] = channel
            logger.info(f"Declared exchange {exchange_name}")
        return self._exchanges[exchange_name]

    def publish_message(self, exchange_name: str,  data: dict, routing_key: str = "",):
        """
        Manda un messaggio a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
            data (dict): Dati dell'evento.
            routing_key (str): Tipo di evento.
        """
        channel = self.declare(exchange_name)

        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(data).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2  # rendo il messaggio persistente
            )
        )

        logger.info(f"Sent message to exchange {exchange_name}. Type: {type}")

    def close(self):
        """Chiude la connessione RabbitMQ e tutti i canali aperti.
        """
        for exchange_name in list(self._threads.keys()):
            self.unsubscribe(exchange_name)
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("Closed RabbitMQ connection")


def declare_services_exchanges(exchanges: dict[str, list[str] | None]):
    """
    Dichiara gli exchange dei servizi e si iscrive a quelli con callback definiti.
    
    Args:
        exchanges (dict[str, list[str] | None], optional): Dizionario con gli exchange e le chiavi di routing.
            Per ascoltare tutti i messaggi, mettere "all".
            Ex {
                "users": {"add" : callback, "update" : callback, ...},
                "auth": {"all" : callback},
            }.
    """
    broker_instance = BrokerSingleton()
    if broker_instance is None:
        logger.error("Broker instance is None, cannot declare exchanges.")
        return

    for exchange, keys in exchanges.items():
        if keys:
            for key in keys:
                broker_instance.subscribe(exchange, keys[key], routing_key=key if key != "all" else "")
