from __future__ import annotations

import logging
from typing import Optional

import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth import jwt

logger = logging.getLogger(__name__)


class GoogleAuthClient:

    ## Defaults
    DEFAULT_SCOPE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    LOGIN_SCOPE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    LOGIN_CALLBACK_PATH_POSTFIX = "login"
    GMAIL_CALLBACK_PATH_POSTFIX = "gmail"

    ## Config keys
    SECRETS_FILE_KEY = "GOOGLE_OAUTH_SECRETS_FILE"  # required
    CALLBACK_URL_KEY = "GOOGLE_OAUTH_CALLBACK_URL"  # required
    SCOPE_KEY = "GOOGLE_OAUTH_SCOPE"  # optional

    config: dict = None

    def __init__(self, config: dict = {}):
        self.config = config
        assert self.config.get(self.SECRETS_FILE_KEY) != None
        assert self.config.get(self.CALLBACK_URL_KEY) != None
        if self.config.get(self.SCOPE_KEY) == None:
            self.config[self.SCOPE_KEY] = self.DEFAULT_SCOPE

    def get_google_login_url(self):
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.config.get(self.SECRETS_FILE_KEY), self.LOGIN_SCOPE,
        )
        flow.redirect_uri = self._create_callback_url(self.LOGIN_CALLBACK_PATH_POSTFIX)

        authorization_url, state = flow.authorization_url(prompt="select_account")
        return authorization_url, state

    def validate_google_login(self, auth_resp_url: str):
        """Validates the code given by the callback and returns the email address of the google user"""
        flow: google_auth_oauthlib.flow.Flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.config.get(self.SECRETS_FILE_KEY), scopes=self.LOGIN_SCOPE,
        )
        flow.redirect_uri = self._create_callback_url(self.LOGIN_CALLBACK_PATH_POSTFIX)
        flow.fetch_token(authorization_response=auth_resp_url)
        credentials: google.oauth2.credentials.Credentials = flow.credentials
        email = jwt.decode(credentials.id_token, verify=False).get("email")
        return email

    def get_gmail_auth_url(self):
        """Build a URL to redirect users to allowing them to grant Redwood access to their google account"""

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.config.get(self.SECRETS_FILE_KEY), self.config.get(self.SCOPE_KEY),
        )
        flow.redirect_uri = self._create_callback_url(self.GMAIL_CALLBACK_PATH_POSTFIX)

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account",
        )

        return authorization_url, state

    def validate_gmail_auth(self, auth_resp_url: str, google_state: str):
        """Validate google oauth callback credentials for granting gmail permissions

        Args:
            auth_resp_url (str): URL with token (callback from Google)
            google_state (str): state of oauth flow for user

        Returns:
            google.oauth2.credentials.Credentials: Google credentials for user
        """

        flow: google_auth_oauthlib.flow.Flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.config.get(self.SECRETS_FILE_KEY),
            scopes=self.config.get(self.SCOPE_KEY),
            state=google_state,
        )
        flow.redirect_uri = self._create_callback_url(self.GMAIL_CALLBACK_PATH_POSTFIX)
        flow.fetch_token(authorization_response=auth_resp_url)
        credentials: google.oauth2.credentials.Credentials = flow.credentials
        return credentials

    def _create_callback_url(self, path_postfix: str):
        """Creates callback url using path given in config + the postfix input"""
        base_url: str = self.config[self.CALLBACK_URL_KEY]
        if not base_url.endswith("/"):
            base_url += "/"
        return base_url + path_postfix
