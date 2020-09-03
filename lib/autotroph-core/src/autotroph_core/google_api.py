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

    def _gmail_service(self) -> Resource:
        if self.gmail_service == None:
            if self.credentials == None:
                logger.error("GmailClient object was not initialized with credentials.")
                raise Exception(
                    "GmailClient object was not initialized with credentials."
                )
            self.gmail_service = build("gmail", "v2", credentials=self.credentials)
        return self.gmail_service
