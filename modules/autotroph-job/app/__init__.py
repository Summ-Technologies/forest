import logging
from typing import List, Tuple

from . import _config
from .worker import sync_gmail

logger = logging.getLogger(__name__)


def run(config: dict):
    logger.debug(f"Setting config object with values: {config}")
    _config.config.update(config)
    sync_gmail()
