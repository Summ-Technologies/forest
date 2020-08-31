from flask_restful import Api

from .controllers import article, triage

V1_PREFIX = "/v1.0"


def route_v1(path: str):
    return "/api" + V1_PREFIX + path


def add_routes(api: Api):
    api.add_resource(triage.BoxListController, route_v1("/user/boxes"))
    api.add_resource(
        article.BoxArticlesListController, route_v1("/user/boxes/<int:id>/articles")
    )
    api.add_resource(article.ArticleController, route_v1("/user/articles/<int:id>"))
    api.add_resource(
        article.BookmarkController, route_v1("/user/articles/<int:id>/bookmark")
    )
    api.add_resource(triage.TriageController, route_v1("/user/triages"))

    api.add_resource(article.NewArticleController, route_v1("/user/admin/articles"))
