from __future__ import annotations

import email.utils
import logging
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import google.oauth2.credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

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

    def get_new_emails(self, history_id: str) -> Tuple[List[str], str]:
        """
        Returns new emails added since history_id and the current_history_id
        TODO: exception handling when history_list with given id returns a 404
        """
        new_email_ids = []
        current_history_id = None

        if history_id is None:
            gmail_service = self.get_gmail_service()
            two_weeks_ago = datetime.utcnow() - timedelta(
                days=15
            )  # 2weeks + 1day to be safe
            query = f"after:{two_weeks_ago.strftime('%Y/%m/%d')}"

            next_page_token = None
            is_first = True
            while next_page_token != None or is_first:
                message_list_resp = (
                    gmail_service.users()
                    .messages()
                    .list(
                        userId="me",
                        maxResults=500,
                        pageToken=next_page_token,
                        q=query,
                    )
                    .execute()
                )
                next_page_token = message_list_resp.get("nextPageToken", None)
                _message_ids = list(
                    map(
                        lambda mess: mess.get("id"),
                        message_list_resp.get("messages", []),
                    )
                )
                new_email_ids.extend(_message_ids)
                if is_first:
                    is_first = False
                    ### To get the current history id, get message data for first message in inbox
                    ### See for more details: https://developers.google.com/gmail/api/guides/sync
                    if len(_message_ids):
                        first_message_id = _message_ids[0]
                        current_history_id = (
                            gmail_service.users()
                            .messages()
                            .get(userId="me", id=first_message_id, format="minimal")
                            .execute()
                            .get("historyId")
                        )
        else:
            is_first = True
            next_page_token = None
            while next_page_token != None or is_first:
                (
                    _new_email_ids,
                    next_page_token,
                    current_history_id,
                ) = self._list_history(history_id, None)
                new_email_ids.extend(_new_email_ids)
                if is_first:
                    is_first = False

        return new_email_ids, current_history_id

    def _list_history(
        self, history_id: str, page_token: str
    ) -> Tuple[List[str], Optional[str], str]:
        """Return Tuple[message_ids, nextPageToken, currentHistoryId]"""
        gmail_service = self.get_gmail_service()
        message_ids = []
        history_response = (
            gmail_service.users()
            .history()
            .list(
                userId="me",
                startHistoryId=history_id,
                pageToken=page_token,
                historyTypes="messageAdded",
            )
            .execute()
        )
        nextPageToken = history_response.get("nextPageToken")
        current_history_id = history_response.get("historyId")
        histories = history_response.get("history", [])
        for history in histories:
            messages_added = history.get("messagesAdded", [])
            for message_added in messages_added:
                message_added_id = message_added.get("message", {}).get("id")
                if message_added_id != None:
                    message_ids.append(message_added_id)
        return message_ids, nextPageToken, current_history_id

    def get_email(self, gmail_message_id: str, format: str = "full") -> Optional[dict]:
        gmail_service = self.get_gmail_service()
        try:
            gmail_message = (
                gmail_service.users()
                .messages()
                .get(userId="me", id=gmail_message_id, format=format)
                .execute()
            )
        except HttpError as e:
            if e.resp.status == 404:
                return None
            else:
                logger.error(f"Error getting email with exception", exc_info=HttpError)
                return None
        return gmail_message

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
    def get_email_from_address(gmail_message: str) -> Tuple[str, str]:
        """Get sender of an email given the email id.

        Args:
            gmail_id (str): id of email in question

        Returns:
            Tuple[str, str]: (name, email address)
        """
        sender_address = GoogleApiClient.get_header_by_name(gmail_message, "From")
        if sender_address:
            return email.utils.parseaddr(sender_address[0])

    @staticmethod
    def get_email_html_body(gmail_message) -> Optional[str]:
        """Get the html body from an email.

        Args:
            gmail_id (str): id of gmail message

        Returns:
            str: html string for body
        """
        content_type = GoogleApiClient.get_header_by_name(gmail_message, "Content-Type")
        if content_type and "multipart/alternative" in content_type[0]:
            ## get body from parts
            body_parts = gmail_message.get("payload", {}).get("parts")
            for part in body_parts:
                content_type_header = list(
                    filter(
                        lambda header: header["name"].lower() == "content-type",
                        part.get("headers", []),
                    )
                )
                if content_type_header:
                    content_type = content_type_header[0].get("value")
                    if "html" in content_type.lower():
                        b64enc_body = part.get("body").get("data")
                        return str(urlsafe_b64decode(b64enc_body), "utf-8")
        elif content_type and "html" in content_type[0]:
            ## get body from body
            b64enc_body = gmail_message.get("payload", {}).get("body", {}).get("data")
            if b64enc_body:
                return str(urlsafe_b64decode(b64enc_body), "utf-8")
        logger.warning(
            f"Failed when attempting to get html body from gamil message: {gmail_message}."
        )
        return None

    @staticmethod
    def get_email_text_body(gmail_message: str) -> Optional[str]:
        """Get the text body from an email.

        Args:
            gmail_id (str): id of gmail message

        Returns:
            str: text string for body
        """
        content_type = GoogleApiClient.get_header_by_name(gmail_message, "Content-Type")
        if content_type and "multipart/alternative" in content_type[0]:
            ## get body from parts
            body_parts = gmail_message.get("payload", {}).get("parts")
            for part in body_parts:
                content_type_header = list(
                    filter(
                        lambda header: header["name"].lower() == "content-type",
                        part.get("headers", []),
                    )
                )
                if content_type_header:
                    content_type = content_type_header[0].get("value")
                    if "text/plain" in content_type.lower():
                        b64enc_body = part.get("body").get("data")
                        return str(urlsafe_b64decode(b64enc_body), "utf-8")
        elif content_type and "text/plain" in content_type[0]:
            ## get body from body
            b64enc_body = gmail_message.get("payload", {}).get("body", {}).get("data")
            if b64enc_body:
                return str(urlsafe_b64decode(b64enc_body), "utf-8")
        logger.warning(
            f"Failed when attempting to get text body from gamil message: {gmail_message}."
        )
        return None

    @staticmethod
    def get_header_by_name(gmail_message: str, header_name: str) -> List[str]:
        """Get the value(s) of the header

        Args:
            gmail_message (str): gmail message of the resource type (Message)
                https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message
            header_name (str): name of header

        Returns:
            List[str]: list of values for the header
        """
        values = []
        payload = gmail_message.get("payload", {})
        headers = payload.get("headers", [])
        values = list(
            map(
                lambda header: header.get("value"),
                filter(
                    lambda header: header.get("name") != None
                    and header.get("name").lower() == header_name.lower(),
                    headers,
                ),
            )
        )
        return values

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
