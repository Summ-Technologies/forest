import logging

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from redwood_core.user_manager import UserManager
from redwood_db.user import User
from redwood_rabbitmq.message_types import ConnectedGoogleAccountMessage

from . import db
from ._config import config

logger = logging.getLogger(__name__)


def import_gmail_newsletters(
    channel, method_frame, header_frame, message: ConnectedGoogleAccountMessage
):
    logger.info(f"Starting gmail newsletter import for {message.serialize()}")
    # Acking message
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Configurable parameters
    resultsPerPage = 500
    numPages = 3

    # Object setup
    session = db.setup_db_session(config["SQLALCHEMY_DATABASE_URI"])
    user_manager = UserManager(session=session, config=config)
    content_manager = ContentManager(session=session, config=config)
    triage_manager: TriageManager = TriageManager(session=session, config=config)

    # Setup Logic
    user: User = session.query(User).get(message.user_id)
    google_api_client = user_manager._get_google_api_client(user)
    gmail_service = google_api_client.get_gmail_service()

    threadIds = set([])
    nextPageToken = None
    for _ in range(numPages):
        message_list_resp = (
            gmail_service.users()
            .messages()
            .list(userId="me", maxResults=resultsPerPage, pageToken=nextPageToken)
            .execute()
        )
        nextPageToken = message_list_resp.get("nextPageToken")
        messages = message_list_resp.get("messages")
        # check if should add messages
        for message in messages:
            gmail_message_id = message.get("id")
            if content_manager.is_email_newsletter(user, gmail_message_id):
                logger.info(
                    f"{user} gmail message id: {gmail_message_id} will be imported as whittle email."
                )
                new_article = content_manager.create_new_article_from_gmail(
                    user, gmail_message_id
                )
                box = list(
                    filter(
                        lambda box: box.name.lower() == "inbox",
                        triage_manager.get_boxes_for_user(user),
                    )
                )[0]
                triage_manager.create_new_triage(new_article, box)
                content_manager.commit_changes()
    logger.info(f"Completed gmail newsletter import for {message.serialize()}")
