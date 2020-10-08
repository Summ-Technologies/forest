import logging

from flask import g
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from redwood_core.content_manager import ContentManager
from redwood_core.user_manager import UserManager
from redwood_db.user import User
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
user_manager: UserManager = manager_factory.get_manager("user")
content_manager: ContentManager = manager_factory.get_manager("content")


class UserGoogleAccountController(Resource):
    @jwt.requires_auth
    def get(self):
        email = user_manager.get_google_account_email(g.user)
        if email:
            ret = {"email": email}
            return responses.success(ret)
        else:
            return responses.error(
                "Google account credentials do not exist or have expired."
            )


class UserController(Resource):
    @jwt.requires_auth
    def get(self):
        """Get's user model for currently logged in user."""
        return responses.success({"user": g.user.to_json()})


class UserConfigAutoArchiveController(Resource):
    put_body = {"auto_archive": fields.Boolean(dataKey="autoArchive", required=True)}

    @jwt.requires_auth
    @use_args(put_body, location="json")
    def put(self, put_args):
        """Update user config option for gmail_auto_archive"""
        do_auto_archive = put_args["auto_archive"]
        user_config = user_manager.set_auto_archive_config(g.user, do_auto_archive)
        user_manager.commit_changes()
        if user_config:
            return responses.success(user_config.to_json())
        return responses.error("Something went wrong")


class UserSubscriptionController(Resource):
    post_args = {"from_address": fields.Email(data_key="fromAddress", required=True)}

    @jwt.requires_auth
    @use_args(post_args, location="json")
    def post(self, args: dict):
        from_address = args["from_address"]
        existing_subscription = content_manager.get_subscription_by_from_address(
            from_address
        )
        if existing_subscription:
            subscription = existing_subscription
        else:
            subscription = content_manager.create_subscription(from_address)
        if not subscription:
            return responses.error("Something went wrong", 500)
        new_user_subscription = user_manager.add_user_subscription(g.user, subscription)
        user_manager.commit_changes()
        return responses.success("Success")
