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


class ArticlesListController(Resource):
    query_args = {"articleIds": fields.List(fields.Integer(), required=True)}

    @jwt.requires_auth
    @use_args(query_args, location="querystring")
    def get(self, args: dict):
        """Gets article data for given ids

        Args:
            args ({'articleIds': List[int]}): [description]

        Returns:
            200, {'articles': [Article.to_json(), ...]}
        """
        articles = content_manager.get_articles_by_id(g.user, id, args["articleIds"])
        return responses.success(
            {"articles": [article.to_json() for article in articles]}
        )


class BoxArticlesListController(Resource):
    @jwt.requires_auth
    def get(self, id: int):
        """
        Get articles ids for box with id.
        """
        article_ids = content_manager.get_articles_by_box_id(g.user, id)
        return responses.success({"article_ids": article_ids})


class ArticleSearchController(Resource):
    query_args = {"query": fields.String(required=True, data_key="q")}

    @jwt.requires_auth
    @use_args(query_args, location="querystring")
    def get(self, args: dict):
        """
        Gets article ids matching search query, sorted by box id of that article.
        """
        ret = {}
        user_boxes = triage_manager.get_boxes_for_user(g.user)
        for box in user_boxes:
            article_ids = content_manager.get_articles_by_search_query(
                g.user, box.id, args["query"].lower()
            )
            ret.update({box.id: article_ids})

        return responses.success(ret)


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
