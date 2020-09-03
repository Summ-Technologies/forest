from __future__ import annotations

import logging
from typing import Optional

import google.oauth2.credentials
import google_auth_oauthlib.flow

logger = logging.getLogger(__name__)


class GoogleAuthClient:

    ## Defaults
    DEFAULT_SCOPE = [
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

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

    def get_google_auth_url(self):
        """Build a URL to redirect users to allowing them to grant Redwood access to their google account"""

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.config.get(self.SECRETS_FILE_KEY), self.config.get(self.SCOPE_KEY),
        )
        flow.redirect_uri = self.config.get(self.CALLBACK_URL_KEY)

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true",
        )

        return authorization_url, state

    def validate_google_auth(self, auth_resp_url: str, google_state: str):
        """Validate google oauth callback credentials

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
        flow.redirect_uri = self.config.get(self.CALLBACK_URL_KEY)
        flow.fetch_token(authorization_response=auth_resp_url)
        credentials: google.oauth2.credentials.Credentials = flow.credentials
        return credentials
