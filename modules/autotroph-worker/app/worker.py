import logging

from redwood_rabbitmq.message_types import ConnectedGoogleAccountMessage

from ._config import config

logger = logging.getLogger(__name__)


def import_gmail_newsletters(
    channel, method_frame, header_frame, message: ConnectedGoogleAccountMessage
):
    logger.info(f"Importing gmail newsletters, {message}")
    logger.info(f"config: {config}")
