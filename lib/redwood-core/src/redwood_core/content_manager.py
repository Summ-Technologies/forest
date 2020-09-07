import logging
from typing import Optional

from redwood_db.content import Article
from redwood_db.triage import Box, Triage
from redwood_db.user import User

from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    def create_new_article(
        self, user: User, title: str, source: str, content: str, html_content: str
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
        article.content = content
        article.html_content = html_content
        article.user_id = user.id
        self.session.add(article)
        self.session.flush()

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
