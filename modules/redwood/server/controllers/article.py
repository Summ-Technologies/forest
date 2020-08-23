import logging

from flask import g
from flask_restful import Resource

from redwood_core.content_manager import ContentManager
from summn_web import responses

from .. import jwt, manager_factory

logger = logging.getLogger(__name__)
content_manager: ContentManager = manager_factory.get_manager("content")


class ArticleController(Resource):
    @jwt.requires_auth
    def get(self, id):
        article = content_manager.get_article_by_id(id)
        if article is None:
            logger.info(f"Trying to get article with id={id} but it doesn't exists")
            return responses.error("Article not found.", 404)
        return responses.success(article.to_json())


class BoxArticlesListController(Resource):
    @jwt.requires_auth
    def get(self, id: int):
        """
        Get articles for box with id.
        """
        articles = content_manager.get_articles_by_box_id(g.user, id)
        return responses.success(list(map(lambda article: article.to_json(), articles)))
