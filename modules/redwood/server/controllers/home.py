import logging

from flask import g
from flask_restful import Resource

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from redwood_core.user_manager import UserManager
from redwood_db.user import User
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
user_manager: UserManager = manager_factory.get_manager("user")
triage_manager: TriageManager = manager_factory.get_manager("triage")
content_manager: ContentManager = manager_factory.get_manager("content")


class UserHomeController(Resource):
    @jwt.requires_auth
    def get(self):
        """
        Returns object like:
        {
            'user': User.to_json,
            'boxes': List[Box.to_json]
            'boxes_articles_count': Map[Box.id -> int]
        }
        """
        # Get currently logged in user
        user = g.user.to_json()
        # Get list of boxes for the user
        boxes = triage_manager.get_boxes_for_user(g.user)
        # Get count of articles per box
        boxes_count = {
            box.id: content_manager.get_num_articles_by_box_id(g.user, box.id)
            for box in boxes
        }

        user_config, new_config = user_manager.get_user_config(g.user)
        if new_config:
            user_manager.commit_changes()
        ## JSON
        ret = {
            "user": g.user.to_json(),
            "boxes": list(map(lambda box: box.to_json(), boxes)),
            "boxes_articles_count": boxes_count,
            "user_config": user_config.to_json(),
        }
        return responses.success(ret)
