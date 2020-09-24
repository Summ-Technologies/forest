from flask_restful import Api

from .controllers import article, auth, home, triage, user

V1_PREFIX = "/v1.0"


def route_v1(path: str):
    return "/api" + V1_PREFIX + path


def add_routes(api: Api):

    ###### /auth ######
    api.add_resource(auth.LoginController, route_v1("/auth/login"))
    api.add_resource(auth.GoogleLoginController, route_v1("/auth/google/login"))
    api.add_resource(
        auth.GoogleLoginCallbackController, route_v1("/auth/google/login/callback")
    )
    api.add_resource(auth.GoogleSignupController, route_v1("/auth/google/signup"))
    api.add_resource(
        auth.GoogleSignupCallbackController, route_v1("/auth/google/signup/callback")
    )
    api.add_resource(auth.GmailPermissionsController, route_v1("/auth/google/gmail"))
    api.add_resource(
        auth.GmailPermissionsCallbackController, route_v1("/auth/google/gmail/callback")
    )

    ###### /user ######

    # /user/home
    api.add_resource(home.UserHomeController, route_v1("/user/home"))

    # /user/boxes
    api.add_resource(triage.BoxListController, route_v1("/user/boxes"))
    api.add_resource(
        article.BoxArticlesListController, route_v1("/user/boxes/<int:id>/articles")
    )

    # /user/triages
    api.add_resource(triage.TriageController, route_v1("/user/triages"))

    # /user/articles
    api.add_resource(article.ArticlesListController, route_v1("/user/articles"))
    api.add_resource(article.ArticleController, route_v1("/user/articles/<int:id>"))
