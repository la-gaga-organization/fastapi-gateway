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
    _exchanges = {}
    _service_name = ""

    def __new__(cls):
        if cls._instance is None:
            setup_logging()
            logger.info("Starting broker consumer...")
            cls._instance = super().__new__(cls)
            cls.exchanges = {}
        return cls._instance

    def __init__(self, service_name: str = settings.SERVICE_NAME):
        self.service_name = service_name
        self._stop_events = {}

    def create_connection(self):
        try:
            credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    credentials=credentials
                )
            )
            if connection.is_open:
                logger.info("Connected to RabbitMQ")
                return connection
            else:
                logger.error("Failed to connect to RabbitMQ")
                raise ConnectionError("Failed to connect to RabbitMQ")
        except Exception as e:
            logger.exception(f"Error connecting to RabbitMQ: {str(e)}")
            return None

    def subscribe(self, exchange_name: str, callback, ex_type: str = "direct", routing_key: str = ""):
        """Iscrive a un exchange RabbitMQ e inizia a consumare i messaggi.

        Args:
            exchange_name (str): Nome dell'exchange.
            callback (function): Funzione di callback per gestire i messaggi ricevuti.
            ex_type (str, optional): Tipo di exchange. Defaults to "direct".
            routing_key (str, optional): Chiave di routing. Defaults to "". Lascia vuoto per ricevere tutti i messaggi.
        """
        key = (exchange_name, routing_key)
        if key in self._exchanges:
            logger.warning(f"Already subscribed to exchange {exchange_name}")
            return

        stop_event = threading.Event()
        self._stop_events[key] = stop_event

        def wrapped_callback(ch, method, properties, body):
            callback(ch, method, properties, body)
            if stop_event.is_set():
                ch.stop_consuming()

        def consume():
            connection = self.create_connection()
            if connection is None:
                logger.error("Cannot start consuming without a valid connection.")
                return
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange_name, exchange_type=ex_type)
            queue_result = channel.queue_declare(
                queue=f'{self.service_name}.{exchange_name}.{routing_key if routing_key else "all"}',
                exclusive=False,
                durable=True,
                auto_delete=False
            )
            queue_name = queue_result.method.queue
            channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
            channel.basic_consume(queue=queue_name, on_message_callback=wrapped_callback, auto_ack=True)
            logger.info(f"Subscribed to exchange {exchange_name} with routing key '{routing_key}'")
            try:
                channel.start_consuming()
            except Exception as e:
                logger.info(f"Stopped consuming for exchange {exchange_name}: {e}")
            finally:
                channel.close()
                connection.close()

        thread = threading.Thread(target=consume, daemon=True)
        thread.start()
        self._exchanges[key] = thread
        logger.info(f"Started consuming in a separate thread for exchange {exchange_name}")

    def unsubscribe(self, exchange_name: str, routing_key: str = ""):
        """Annulla l'iscrizione a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
            routing_key (str, optional): Chiave di routing. Defaults to "".
        """
        key = (exchange_name, routing_key)
        if key in self._exchanges:
            if key in self._stop_events:
                self._stop_events[key].set()  # segnala lo stop al thread
            thread = self._exchanges[key]
            thread.join(timeout=2)
            del self._exchanges[key]
            del self._stop_events[key]
            logger.info(f"Stopped consumer thread for exchange {exchange_name} with routing key '{routing_key}'")

    def publish_message(self, exchange_name: str, event_type: str, data: dict, routing_key: str = ""):
        """
        Manda un messaggio a un exchange RabbitMQ.

        Args:
            exchange_name (str): Nome dell'exchange.
            event_type (str): Tipo di evento.
            data (dict): Dati dell'evento.
            routing_key (str, optional): Chiave di routing. Defaults to "".
        """
        connection = self.create_connection()
        if connection is None:
            logger.error("Cannot publish message without a valid connection.")
            return

        channel = connection.channel()
        channel.exchange_declare(exchange=exchange_name, exchange_type="direct")

        message = {
            "type": event_type,
            "data": data
        }

        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2  # rendo il messaggio persistente
            )
        )

        channel.close()
        connection.close()

        logger.info(f"Sent message to exchange {exchange_name}. Type: {event_type}")

    def close(self):
        """Chiude tutti i thread consumer RabbitMQ."""
        for key in list(self._exchanges.keys()):
            exchange_name, routing_key = key
            self.unsubscribe(exchange_name, routing_key)
        logger.info("Closed all RabbitMQ consumer threads")


def declare_services_exchanges(exchanges: dict):
    """Dichiara e sottoscrive agli exchange RabbitMQ specificati nel dizionario exchanges.

    Args:
        exchanges (dict): Dizionario {exchange: callback}
    """
    broker_instance = BrokerSingleton()
    if broker_instance is None:
        logger.error("Broker instance is None, cannot declare exchanges.")
        return

    for exchange, callback in exchanges.items():
        broker_instance.subscribe(exchange, callback)
