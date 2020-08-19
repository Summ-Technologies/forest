from flask_restful import Api

from .controllers import article

V1_PREFIX = "/v1"


def route_v1(path: str):
    return "/api" + V1_PREFIX + path


def add_routes(api: Api):
    api.add_resource(article.ArticleController, route_v1("/article/<int:id>"))
