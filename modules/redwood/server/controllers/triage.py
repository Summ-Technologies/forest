import logging

from flask import g
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

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


class TriageController(Resource):
    post_args = {
        "article_id": fields.Integer(data_key="articleId", required=True),
        "box_id": fields.Integer(data_key="boxId", required=True),
    }

    @jwt.requires_auth
    @use_args(post_args, location="json")
    def post(self, args):
        """
        Move an article into a new box.
        """
        new_triage = triage_manager.triage_article(
            g.user, args.get("article_id"), args.get("box_id")
        )
        triage_manager.commit_changes()
        return responses.success(None)
