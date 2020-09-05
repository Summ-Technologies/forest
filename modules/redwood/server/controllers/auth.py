import logging

from flask import g, request
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from redwood_core.user_manager import UserManager
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
user_manager: UserManager = manager_factory.get_manager("user")


class LoginController(Resource):

    post_args = {
        "email": fields.Email(required=True),
        "password": fields.String(required=True),
    }

    @use_args(post_args)
    def post(self, args):
        """Validate user credentials and return JWT Token"""
        email, password = args["email"], args["password"]
        login_user = user_manager.authenicate_user(email, password)
        if login_user:
            cookie_name = jwt.jwt_cookie_name
            jwt_token = jwt.encode_jwt(login_user.login_id)
            headers = {"Set-Cookie": f"{cookie_name}={jwt_token}; Path=/; HttpOnly"}
            ret = {"user": login_user.to_json()}
            return responses.success(ret, extra_headers=headers)
        return responses.error("Invalid email or password.", 422)


class GoogleLoginController(Resource):
    @jwt.requires_auth
    def get(self):
        google_auth_url = user_manager.google_oauth_step1(g.user)
        user_manager.commit_changes()
        ret = {"redirect_url": google_auth_url}
        return responses.success(ret)


class GoogleLoginCallbackController(Resource):
    post_args = {"callback_url": fields.String(required=True)}

    @jwt.requires_auth
    @use_args(post_args)
    def post(self, args):
        user_manager.google_oauth_callback(g.user, args["callback_url"])
        user_manager.commit_changes()
