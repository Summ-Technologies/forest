import logging
from typing import Optional

from redwood_db.content import Article, TagToArticle

from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    def get_article_by_id(self, id) -> Optional[Article]:
        return self.session.query(Article).get(id)
