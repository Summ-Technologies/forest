import logging

from redwood_core.factory import ManagerFactory
from redwood_db.content import Article
from redwood_db.user import User
from redwood_rabbitmq.message_types import ConnectedGoogleAccountMessage

from . import db
from ._config import config

logger = logging.getLogger(__name__)


def import_gmail_newsletters(
    channel, method_frame, header_frame, message: ConnectedGoogleAccountMessage
):
    logger.info(f"Starting gmail newsletter import for {message.serialize()}")

    # Object setup
    session = db.setup_db_session(config["SQLALCHEMY_DATABASE_URI"])
    factory = ManagerFactory(session, config)

    user_manager = factory.get_manager("user")
    content_manager = factory.get_manager("content")
    triage_manager = factory.get_manager("triage")

    # Setup Logic
    user: User = session.query(User).get(message.user_id)
    gmail_api_client = user_manager.get_gmail_api_client(user)
    gmail_service = gmail_api_client.get_gmail_service()

    messages = content_manager.get_new_emails(user)
    # check if should add messages
    for gmail_message_id in messages:
        if content_manager.is_email_newsletter(user, gmail_message_id):
            gmail_message = gmail_api_client.get_email(gmail_message_id)
            if gmail_message:
                logger.info(
                    f"{user} gmail message id: {gmail_message_id} will be imported as whittle email."
                )
                new_article = content_manager.create_new_article_from_gmail(
                    user, gmail_message
                )
                if new_article:
                    if "UNREAD" not in gmail_message.get("labelIds"):
                        box = triage_manager.get_user_library(user)
                        triage_manager.create_new_triage(new_article, box)
                content_manager.commit_changes()
    logger.info(f"Completed gmail newsletter import for {message.serialize()}")
    # Acking message
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    logger.info(f"Acking message {message.serialize()}")
    session.close()
