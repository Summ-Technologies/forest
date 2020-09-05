import logging
from typing import List, Tuple

import pika

from redwood_rabbitmq.connection import RMQConnection
from redwood_rabbitmq.consume import RMQConsumer
from redwood_rabbitmq.queue import NEW_GOOGLE_ACCOUNT_CONNECTED, BaseQueue

from . import _config
from .worker import import_gmail_newsletters

logger = logging.getLogger(__name__)

queues: List[Tuple[BaseQueue, callable]] = [
    (NEW_GOOGLE_ACCOUNT_CONNECTED, import_gmail_newsletters)
]


def run(config: dict):
    logger.info("Starting consumer...")
    logger.debug(f"Setting config object with values: {config}")
    _config.config.update(config)
    rmq_connection = RMQConnection(config=_config.config)
    for queue_callback in queues:
        logger.info("Adding queue %s.", queue_callback[0].queue_name)
        consumer = RMQConsumer(queue=queue_callback[0], connection=rmq_connection)
        consumer.setup_consumer(queue_callback[1])
    rmq_connection.get_channel().start_consuming()
    logger.info("Stopped consuming.")
    rmq_connection.teardown()
    logger.info("Connection torn down. Consumer closing...")
