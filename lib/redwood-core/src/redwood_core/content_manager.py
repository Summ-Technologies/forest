import logging
from typing import Optional

from autotroph_core.google_api import GoogleApiClient
from redwood_db.content import Article
from redwood_db.triage import Box, Triage
from redwood_db.user import User

from .factory import ManagerFactory
from .user_manager import UserManager

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    def is_email_newsletter(self, user: User, gmail_message_id: str) -> bool:
        """Returns if the gmail message a newsletter that should be imported.

        Args:
            user (User):
            gmail_message_id (str): gmail's id of email

        Returns:
            bool: is email whittle newsletter
        """
        user_manager: UserManager = self.get_manager("user")
        gmail_api_client = user_manager._get_gmail_api_client(user)
        from_address = gmail_api_client.get_email_from_address(gmail_message_id)
        # TODO add logic determining if a message is a newsletter (like checking user's subscriptions in db)
        if "@substack.com" in from_address.lower():
            return True
        return False

    def create_new_article_from_gmail(
        self, user: User, gmail_message_id: str
    ) -> Optional[Article]:
        """Retrieves email from gmail and saves data as new article record.

        Args:
            user (User): [description]
            gmail_message_id (str): [description]
        
        Returns:
            (Article): newly added and flushed article record
        """
        user_manager: UserManager = self.get_manager("user")
        gmail_api_client = user_manager._get_gmail_api_client(user)
        gmail_message = (
            gmail_api_client.get_gmail_service()
            .users()
            .messages()
            .get(userId="me", id=gmail_message_id)
            .execute()
        )
        title = GoogleApiClient.get_header_by_name(gmail_message, "Subject")[0]
        source = GoogleApiClient.get_header_by_name(gmail_message, "From")[0]
        html_content = gmail_api_client.get_email_html_body(gmail_message_id)
        text_content = gmail_api_client.get_email_text_body(gmail_message_id)
        return self.create_new_article(
            user,
            title,
            source,
            author=None,
            outline=None,
            text_content=text_content,
            html_content=html_content,
            gmail_message_id=gmail_message_id,
        )

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
