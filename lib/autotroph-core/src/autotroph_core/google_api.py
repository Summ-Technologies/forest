from __future__ import annotations

import logging
from typing import Optional

import google.oauth2.credentials
from googleapiclient.discovery import Resource, build

logger = logging.getLogger(__name__)


class GoogleApiClient:
    credentials: Optional[google.oauth2.credentials.Credentials] = None
    gmail_service: Optional[Resource] = None

    def __init__(self, credentials: google.oauth2.credentials.Credentials):
        self.credentials = credentials

    def get_gmail_service(self) -> Resource:
        if self.gmail_service == None:
            if self.credentials == None:
                logger.error("GmailClient object was not initialized with credentials.")
                raise Exception(
                    "GmailClient object was not initialized with credentials."
                )
            self.gmail_service = build("gmail", "v1", credentials=self.credentials)
        return self.gmail_service

    def get_user_profile(self) -> dict:
        """Get gmail user profile for the user with credentials associated to this object

        Returns:
            dict: See http://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.users.html#getProfile
            {
                "emailAddress": <str>,
                "messagesTotal": <int>,
                "threadsTotal": <int>,
                "historyId": <str>
            }
        """
        gmail_service = self.get_gmail_service()
        profile = gmail_service.users().getProfile(userId="me").execute()
        return profile

    @staticmethod
    def init_api_client(credentials_json: str) -> GoogleApiClient:
        """Creates api client given credentials as json

        Args:
            credentials_json (str): User crendentials in json string

        Returns:
            GoogleApiClient: GoogleApiClient
        """

        credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(
            google.oauth2.credentials.json.loads(credentials_json)
        )
        return GoogleApiClient(credentials)
