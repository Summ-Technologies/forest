import logging

from flask import g
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from redwood_core.content_manager import ContentManager
from redwood_core.triage_manager import TriageManager
from redwood_db.content import Article
from summn_web import responses

from .. import db, jwt, manager_factory

logger = logging.getLogger(__name__)
content_manager: ContentManager = manager_factory.get_manager("content")
triage_manager: TriageManager = manager_factory.get_manager("triage")


class ArticleController(Resource):
    @jwt.requires_auth
    def get(self, id):
        article = content_manager.get_article_by_id(id, g.user)
        if article is None:
            logger.info(f"Trying to get article with id={id} but it doesn't exists")
            return responses.error("Article not found.", 404)
        return responses.success(article.to_json())


class BoxArticlesListController(Resource):
    query_args = {"page": fields.Integer(required=False, missing=0)}

    @jwt.requires_auth
    @use_args(query_args, location="query")
    def get(self, args: dict, id: int):
        """
        Get articles for box with id.
        """
        page = args.get("page", 0)
        articles = content_manager.get_articles_by_box_id(g.user, id, page)
        return responses.success(
            {"articles": list(map(lambda article: article.to_json(), articles))}
        )


class BookmarkController(Resource):
    @jwt.requires_auth
    def post(self, id):
        article = content_manager.get_article_by_id(id, g.user)
        if article:
            content_manager.bookmark_article(article)
            content_manager.commit_changes()
            return responses.success({"article": article.to_json()})
        return responses.error("Article not found", 404)

    @jwt.requires_auth
    def delete(self, id):
        article = content_manager.get_article_by_id(id, g.user)
        if article:
            content_manager.unbookmark_article(article)
            content_manager.commit_changes()
            return responses.success({"article": article.to_json()})
        return responses.error("Article not found", 404)
