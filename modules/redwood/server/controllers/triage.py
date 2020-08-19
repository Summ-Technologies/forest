import logging

from flask import g
from flask_restful import Resource

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
content_manager: ContentManager = manager_factory.get_manager("content")
triage_manager: TriageManager = manager_factory.get_manager("triage")


class BoxListController(Resource):
    @jwt.requires_auth
    def get(self):
        """
        Get all boxes for the logged in user.
        """
        boxes = triage_manager.get_boxes_for_user(g.user)
        return responses.success({"boxes": list(map(lambda box: box.to_json(), boxes))})
