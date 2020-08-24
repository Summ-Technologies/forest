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
        article = content_manager.get_article_by_id(id)
        if article is None:
            logger.info(f"Trying to get article with id={id} but it doesn't exists")
            return responses.error("Article not found.", 404)
        return responses.success(article.to_json())


# TODO Remove this and move to admin console
class NewArticleController(Resource):
    post_args = {
        "title": fields.String(required=True),
        "subjectline": fields.String(required=True),
        "source": fields.String(required=True),
        "content": fields.String(required=True),
        "html_content": fields.String(required=True, data_key="htmlContent"),
        "tags": fields.String(required=True),
    }

    @jwt.requires_auth
    @use_args(post_args, location="json")
    def post(self, args):
        article = Article()
        article.title = args["title"]
        article.subjectline = args["subjectline"]
        article.source = args["source"]
        article.content = args["content"]
        article.html_content = args["html_content"]
        article.tags = args["tags"]
        article.user_id = g.user.id
        db.session.add(article)
        db.session.flush()
        inboxes = list(
            filter(
                lambda box: box.name and box.name.lower() == "inbox",
                triage_manager.get_boxes_for_user(g.user),
            )
        )
        if inboxes:
            triage_manager.triage_article(g.user, article.id, inboxes[0].id)
        db.session.commit()
        return responses.success(None)


class BoxArticlesListController(Resource):
    @jwt.requires_auth
    def get(self, id: int):
        """
        Get articles for box with id.
        """
        articles = content_manager.get_articles_by_box_id(g.user, id)
        return responses.success(list(map(lambda article: article.to_json(), articles)))
