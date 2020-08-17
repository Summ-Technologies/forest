from flask_restful import Api

V1_PREFIX = "/v1"


def route_v1(path: str):
    return "/api" + V1_PREFIX + path


def add_routes(api: Api):
    pass
