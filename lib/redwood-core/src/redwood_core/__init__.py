import logging
from typing import Dict

from sqlalchemy.orm import Session

from .content_manager import ContentManager
from .factory import ManagerFactory
from .triage_manager import TriageManager

logger = logging.getLogger(__name__)

for manager in [("content", ContentManager), ("triage", TriageManager)]:
    ManagerFactory.register_manager(manager[0], manager[1])
