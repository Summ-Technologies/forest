## Controllers here are temporary and help speed up workflows
import logging

from flask import g
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from redwood_core.user_manager import UserManager
from redwood_db.content import Article
from summn_web import responses

from .. import db, jwt, manager_factory

logger = logging.getLogger(__name__)
content_manager: ContentManager = manager_factory.get_manager("content")
user_manager: UserManager = manager_factory.get_manager("user")
triage_manager: TriageManager = manager_factory.get_manager("triage")


# TODO Remove this and move to admin console
class NewUserController(Resource):
    get_args = {"admin_password": fields.String(required=True)}

    post_args = {
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        }

    @use_args(get_args, location="query")
    @use_args(post_args, location="json")
    def post(self, get_args, post_args):
        if get_args["admin_password"].lower() != "password69":
            return responses.error("Admin password was not correct", 422)
        new_user = user_manager.create_user(
            post_args["email"], post_args["first_name"], post_args["last_name"]
        )
        if new_user:
            user_manager.commit_changes()
        return responses.success(new_user.to_json())
