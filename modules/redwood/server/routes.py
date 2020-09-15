from flask_restful import Api

from .controllers import admin, article, auth, triage, user

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

    # /user/google/email
    api.add_resource(user.UserGoogleAccountController, route_v1("/user/google/email"))

    # /user/admin (TODO remove this endpoint)
    api.add_resource(article.NewArticleController, route_v1("/user/admin/articles"))
    api.add_resource(admin.NewUserController, route_v1("/admin/user"))
