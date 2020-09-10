import logging

from bs4 import BeautifulSoup

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from redwood_core.user_manager import UserManager
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
    # Acking message
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Object setup
    session = db.setup_db_session(config["SQLALCHEMY_DATABASE_URI"])
    user_manager = UserManager(session=session, config=config)
    content_manager = ContentManager(session=session, config=config)
    triage_manager: TriageManager = TriageManager(session=session, config=config)

    # Setup Logic
    user: User = session.query(User).get(message.user_id)
    gmail_api_client = user_manager._get_gmail_api_client(user)
    gmail_service = gmail_api_client.get_gmail_service()

    message_list_resp = (
        gmail_service.users()
        .messages()
        .list(
            userId="me",
            maxResults=200,
            q="from:@substack.com",  # TODO remove this, only for making demo better
        )
        .execute()
    )
    messages = message_list_resp.get("messages")
    # check if should add messages
    for email in messages:
        gmail_message_id = email.get("id")
        if content_manager.is_email_newsletter(user, gmail_message_id):
            logger.info(
                f"{user} gmail message id: {gmail_message_id} will be imported as whittle email."
            )
            new_article = content_manager.create_new_article_from_gmail(
                user, gmail_message_id
            )
            outline = _create_outline(new_article)
            new_article.outline = outline
            session.add(new_article)
            session.flush()
            inbox = list(
                filter(
                    lambda box: box.name.lower() == "inbox",
                    triage_manager.get_boxes_for_user(user),
                )
            )[0]
            library = list(
                filter(
                    lambda box: box.name.lower() == "library",
                    triage_manager.get_boxes_for_user(user),
                )
            )[0]
            message_metadata = (
                gmail_service.users()
                .messages()
                .get(userId="me", id=gmail_message_id, format="metadata")
                .execute()
            )
            if "UNREAD" in message_metadata.get("labelIds"):
                triage_manager.create_new_triage(new_article, inbox)
            else:
                triage_manager.create_new_triage(new_article, library)

            content_manager.commit_changes()
    logger.info(f"Completed gmail newsletter import for {message.serialize()}")


def _create_outline(article: Article):
    outline = ""
    soup = BeautifulSoup(article.html_content, "html.parser")
    for header in soup.find_all(["h1", "h2", "h3"]):
        if header.name == "h1":
            outline += f"##### [{header.get_text()}](https://whittle-staging.summn.co/read/{article.id}#)"
            outline += "  \n"
        elif header.name == "h2":
            outline += f"[**{header.get_text()}**](https://whittle-staging.summn.co/read/{article.id}#)"
            outline += "  \n"
        elif header.name == "h3":
            outline += f"- [**{header.get_text()}**](https://whittle-staging.summn.co/read/{article.id}#)"
            outline += "  \n"
    return outline
