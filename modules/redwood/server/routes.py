from flask_restful import Api

from .controllers import article, auth, triage

V1_PREFIX = "/v1.0"


def route_v1(path: str):
    return "/api" + V1_PREFIX + path


def add_routes(api: Api):

    ###### /auth ######
    api.add_resource(auth.LoginController, route_v1("/auth/login"))
    api.add_resource(auth.GoogleLoginController, route_v1("/auth/google/connect"))
    api.add_resource(
        auth.GoogleLoginCallbackController, route_v1("/auth/google/callback")
    )

    ###### /user ######

    # /user/boxes
    api.add_resource(triage.BoxListController, route_v1("/user/boxes"))
    api.add_resource(
        article.BoxArticlesListController, route_v1("/user/boxes/<int:id>/articles")
    )

    # /user/triages
    api.add_resource(triage.TriageController, route_v1("/user/triages"))

    # /user/articles
    api.add_resource(article.ArticleController, route_v1("/user/articles/<int:id>"))
    api.add_resource(
        article.BookmarkController, route_v1("/user/articles/<int:id>/bookmark")
    )

    # /user/admin (TODO remove this endpoint)
    api.add_resource(article.NewArticleController, route_v1("/user/admin/articles"))
