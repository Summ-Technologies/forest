import logging

from redwood_core.factory import ManagerFactory
from redwood_db.user import User

from . import db
from ._config import config

logger = logging.getLogger(__name__)


def sync_gmail():
    logger.info("Starting gmail sync for all users.")

    # Object setup
    session = db.setup_db_session(config["SQLALCHEMY_DATABASE_URI"])
    factory = ManagerFactory(session, config)

    user_manager = factory.get_manager("user")
    content_manager = factory.get_manager("content")

    authenticated_users = user_manager.get_users_with_gmail_permissions()

    for user in authenticated_users:
        # Setup Logic
        user: User
        try:
            logger.info(f"Attempting to update inbox for {user}")
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
                        content_manager.commit_changes()
        except Exception as e:
            logger.warning(
                f"Exception encountered trying to sync gmail for {user}.", exc_info=e
            )
    logger.info(f"Completed gmail sync")
    session.close()
