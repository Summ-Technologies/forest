import logging

from flask import g, request
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from redwood_core.user_manager import UserManager
from redwood_rabbitmq import message_types, queue
from summn_web import responses

from .. import jwt, manager_factory, rmq

logger = logging.getLogger(__name__)
user_manager: UserManager = manager_factory.get_manager("user")
new_gmail_publisher = rmq.get_publisher(queue.NEW_GOOGLE_ACCOUNT_CONNECTED)

## Web args
callback_post_args = {"callback_url": fields.String(required=True)}


class LoginController(Resource):
    @jwt.requires_auth
    def delete(self):
        """Sets empty cookie (to simulate logging out)"""
        cookie_name = jwt.jwt_cookie_name
        return responses.success(
            "Successfully logged out.", 200, {"Set-Cookie": f"{cookie_name}=''" ""}
        )


class GoogleSignupController(Resource):
    def get(self):
        google_auth_url = user_manager.google_signup_step1()
        ret = {"redirect_url": google_auth_url}
        return responses.success(ret)


class GoogleSignupCallbackController(Resource):
    @use_args(callback_post_args)
    def post(self, args):
        new_user = user_manager.google_signup_callback(args["callback_url"])
        if new_user:
            cookie_name = jwt.jwt_cookie_name
            jwt_token = jwt.encode_jwt(new_user.login_id)
            headers = {"Set-Cookie": f"{cookie_name}={jwt_token}; Path=/; HttpOnly"}
            ret = {"user": new_user.to_json()}
            return responses.success(ret, extra_headers=headers)
        else:
            return responses.error(
                "There was an error signing up with google account", 500
            )


class GoogleLoginController(Resource):
    def get(self):
        google_auth_url = user_manager.google_login_step1()
        ret = {"redirect_url": google_auth_url}
        return responses.success(ret)


class GoogleLoginCallbackController(Resource):
    @use_args(callback_post_args)
    def post(self, args):
        login_user = user_manager.google_login_callback(args["callback_url"])
        if login_user:
            cookie_name = jwt.jwt_cookie_name
            jwt_token = jwt.encode_jwt(login_user.login_id)
            headers = {"Set-Cookie": f"{cookie_name}={jwt_token}; Path=/; HttpOnly"}
            ret = {"user": login_user.to_json()}
            return responses.success(ret, extra_headers=headers)
        else:
            return responses.error(
                "There was an error logging in with google account", 500
            )


class GmailPermissionsController(Resource):
    @jwt.requires_auth
    def get(self):
        google_auth_url = user_manager.gmail_permissions_step1(g.user)
        user_manager.commit_changes()
        ret = {"redirect_url": google_auth_url}
        return responses.success(ret)


class GmailPermissionsCallbackController(Resource):
    @jwt.requires_auth
    @use_args(callback_post_args)
    def post(self, args):
        user_manager.gmail_auth_callback(g.user, args["callback_url"])
        user_manager.commit_changes()
        new_gmail_publisher.publish(
            message_types.ConnectedGoogleAccountMessage(g.user.id)
        )
