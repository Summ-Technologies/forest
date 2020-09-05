import logging

from flask import g
from flask_restful import Resource

from redwood_core.user_manager import UserManager
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
user_manager: UserManager = manager_factory.get_manager("user")


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
