import logging
from typing import List, Optional

from bs4 import BeautifulSoup
from sqlalchemy import and_, exists

from autotroph_core.google_api import GoogleApiClient
from redwood_db.content import Article
from redwood_db.triage import Box, Triage
from redwood_db.user import User

from .factory import ManagerFactory
from .user_manager import UserManager

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    def get_new_emails(self, user: User) -> List[str]:
        """
        Returns message_ids for all emails since history_id.
        If history_id is None then returns all message_ids from the past 2 weeks

        Note, this message adds the current history_id for the given user to the databse
        session so the session does need to be committed after calling this method.
        """
        user_manager = self.get_manager("user")
        gmail_api_client = user_manager.get_gmail_api_client(user)
        history_id = user_manager.get_latest_history_id(user)
        latest_emails, current_history_id = gmail_api_client.get_new_emails(history_id)
        user_manager.create_history_id(user, current_history_id)
        return latest_emails

    def is_email_newsletter(self, user: User, gmail_message_id: str) -> bool:
        """Returns if the gmail message a newsletter that should be imported.

        Args:
            user (User):
            gmail_message_id (str): gmail's id of email

        Returns:
            bool: is email whittle newsletter
        """
        user_manager: UserManager = self.get_manager("user")
        gmail_api_client = user_manager.get_gmail_api_client(user)
        gmail_message = gmail_api_client.get_email(gmail_message_id, format="metadata")
        name, from_address = GoogleApiClient.get_email_from_address(gmail_message)
        # TODO add logic determining if a message is a newsletter (like checking user's subscriptions in db)
        if "@substack.com" in from_address.lower():
            return True
        return False

    def create_new_article_from_gmail(
        self, user: User, gmail_message: dict, move_to_library: bool = False
    ) -> Optional[Article]:
        """Retrieves email from gmail and saves data as new article record.

        Args:
            user (User):
            gmail_message_id (str):
            move_to_library (bool): triage to library instead of inbox
        
        Returns:
            (Article): newly added and flushed article record
        """
        user_manager = self.get_manager("user")
        gmail_message_id = gmail_message["id"]
        title = GoogleApiClient.get_header_by_name(gmail_message, "Subject")[0]
        author, source = GoogleApiClient.get_email_from_address(gmail_message)
        html_content = GoogleApiClient.get_email_html_body(gmail_message)
        text_content = GoogleApiClient.get_email_text_body(gmail_message)
        outline = self.generate_outline(html_content)
        ((gmail_message_exists,),) = self.session.query(
            exists().where(
                and_(
                    Article.gmail_message_id == gmail_message_id,
                    Article.user_id == user.id,
                )
            )
        )
        if gmail_message_exists:
            logger.warning(
                f"{user} attempting to create article from email with id: {gmail_message_id} but this id exists in the articles table already."
            )
        else:
            new_article = self.create_new_article(
                user,
                title,
                source,
                author=author,
                outline=outline,
                text_content=text_content,
                html_content=html_content,
                gmail_message_id=gmail_message_id,
            )
            if new_article:
                triage_manager = self.get_manager("triage")
                if move_to_library:
                    box = triage_manager.get_user_library(user)
                else:
                    box = triage_manager.get_user_inbox(user)
                triage_manager.create_new_triage(new_article, box)
                return new_article

    def create_new_article(
        self,
        user: User,
        title: str,
        source: str,
        author: str,
        outline: str,
        text_content: str,
        html_content: str,
        gmail_message_id: str,
    ) -> Article:
        """Creates a new article.
        Adds, and flushes, but does not commit the article record.

        Args:
            user (User): user who owns the article
            title (str): title
            source (str): source
            content (str): content
            html_content (str): html_string
        Returns:
            (Article): newly created article record (uncommitted)
        """
        article = Article()
        article.title = title
        article.source = source
        article.author = author
        article.outline = outline
        article.text_content = text_content
        article.html_content = html_content
        article.gmail_message_id = gmail_message_id
        article.user_id = user.id
        self.session.add(article)
        self.session.flush()
        return article

    def get_article_by_id(self, id, user: User = None) -> Optional[Article]:
        """
        Get article by id. If user is passed, only return an article if the user is the owner of the article.
        Return article if article exists, else None
        """
        article: Optional[Article] = self.session.query(Article).get(id)
        if user:
            if article and article.user_id == user.id:
                return article
            else:
                logger.info(
                    f"{user} tried to retrieve article: {article} but was not the owner."
                )
                return None
        else:
            return article

    def get_articles_by_box_id(self, user: User, box_id: int):
        user_articles = self.session.query(Article.id).filter_by(user_id=user.id)
        article_ids = (
            self.session.query(Triage.article_id)
            .filter(Triage.article_id.in_(user_articles))
            .filter_by(box_id=box_id)
            .filter_by(is_active=True)
            .order_by(Triage.created_at.asc())
        )
        return [
            self.session.query(Article).get(article_id)
            for article_id in article_ids.all()
        ]

    def bookmark_article(self, article: Article) -> Article:
        """Add bookmarked to article"""
        if not article.bookmarked:
            article.bookmarked = True
            self.session.add(article)
            self.session.flush()
        return article

    def unbookmark_article(self, article: Article) -> Article:
        """Remove bookmark from article"""
        if article.bookmarked:
            article.bookmarked = False
            self.session.add(article)
            self.session.flush()
        return article

    def generate_outline(self, html_content: str):
        outline = ""
        soup = BeautifulSoup(html_content, "html.parser")
        for header in soup.find_all(["h1", "h2", "h3"]):
            if header.name == "h1":
                outline += f"##### [{header.get_text()}](#)"
                outline += "  \n\n"
            elif header.name == "h2":
                outline += f"[**{header.get_text()}**](#)"
                outline += "  \n\n"
            elif header.name == "h3":
                outline += f"- [**{header.get_text()}**](#)"
                outline += "  \n\n"
        return outline
