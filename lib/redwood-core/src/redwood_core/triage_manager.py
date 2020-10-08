import logging
from typing import Optional

from sqlalchemy import func

from redwood_db.content import Article
from redwood_db.triage import Box, Triage
from redwood_db.user import User

from .content_manager import ContentManager
from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class TriageManager(ManagerFactory):
    def get_box_by_id(self, id: int) -> Box:
        return self.session.query(Box).get(id)

    def get_box_for_article_id(self, user: User, article_id: int):
        content_manager: ContentManager = self.get_manager("content")
        article = content_manager.get_article_by_id(article_id, user)
        box_id = (
            self.session.query(Triage.box_id)
            .filter_by(article_id=article_id)
            .filter_by(is_active=True)
            .one_or_none()
        )
        return self.get_box_by_id(box_id)

    def create_box_for_user(self, user: User, box_name: str):
        new_box = Box()
        new_box.name = box_name
        new_box.user_id = user.id
        self.session.add(new_box)
        self.session.flush()
        return new_box

    def get_boxes_for_user(self, user: User):
        return self.session.query(Box).filter_by(user_id=user.id).all()

    def create_new_triage(self, article: Article, box: Box):
        """Create new triage record and set old ones as inactive"""
        for triage in (
            self.session.query(Triage)
            .filter_by(article_id=article.id)
            .filter_by(is_active=True)
            .all()
        ):
            triage: Triage
            triage.is_active = False
            self.session.add(triage)
        # move the article to the correct box
        new_triage = Triage()
        new_triage.box_id = box.id
        new_triage.article_id = article.id
        new_triage.is_active = True
        self.session.add(new_triage)
        self.session.flush()
        return new_triage

    def triage_article(self, user: User, article_id: int, box_id: int):
        content_manager: ContentManager = self.get_manager("content")
        user_manager = self.get_manager("user")
        (user_config, _) = user_manager.get_user_config(user)
        article = content_manager.get_article_by_id(article_id, user)
        box = self.get_box_by_id(box_id)
        if (article) and (box and box.user_id == user.id):
            # ensure the article doesn't already exist in the correct box
            current_box = self.get_box_for_article_id(user, article.id)
            if not current_box or current_box.id != box.id:
                # mark previous triages as inactive
                triage = self.create_new_triage(article, box)
                library = self.get_user_library(user)
                if box == library and user_config.gmail_auto_archive:
                    logger.info(
                        f"Triaging {article} to {box}. {user_config} has auto archive enabled. Attempting to archive message in gmail"
                    )
                    try:
                        gmail_api_client = user_manager.get_gmail_api_client(user)
                        gmail_api_client.archive_email(article.gmail_message_id)
                    except Exception as e:
                        logger.error(
                            f"Error when trying to archive {article}", exc_info=e
                        )
                elif box == library:
                    logger.info(
                        f"Triaging {article} to {box} but auto archive is disabled"
                    )

            else:
                logger.info(
                    f"{user} tried to triage {article} to {box} but it already existed in that box."
                )

    def get_user_inbox(self, user: User) -> Box:
        return (
            self.session.query(Box)
            .filter(func.lower(Box.name) == "inbox")
            .filter_by(user_id=user.id)
            .one()
        )

    def get_user_library(self, user: User) -> Box:
        return (
            self.session.query(Box)
            .filter(func.lower(Box.name) == "library")
            .filter_by(user_id=user.id)
            .one()
        )
