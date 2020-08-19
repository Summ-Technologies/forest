import logging
from typing import Optional

from redwood_db.triage import Box
from redwood_db.user import User

from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class TriageManager(ManagerFactory):
    def create_box_for_user(self, user: User, box_name: str):
        new_box = Box()
        new_box.name = box_name
        new_box.user_id = user.id
        self.session.add(new_box)
        self.session.flush()
        return new_box

    def get_boxes_for_user(self, user: User):
        return self.session.query(Box).filter_by(user_id=user.id).all()
