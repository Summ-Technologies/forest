import logging
from typing import Optional

from redwood_db.content import Article
from redwood_db.triage import Box, Triage
from redwood_db.user import User

from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    def get_article_by_id(self, id) -> Optional[Article]:
        return self.session.query(Article).get(id)

    def get_articles_by_box_id(self, user: User, box_id: int):
        user_articles = self.session.query(Article.id).filter_by(user_id=user.id)
        return (
            self.session.query(Triage)
            .filter(Triage.article_id.in_(user_articles))
            .filter_by(box_id=box_id)
            .filter_by(is_active=True)
            .all()
        )
