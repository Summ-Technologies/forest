import os
from functools import wraps

from flask import g

import summn_logging
import summn_web
from redwood_core import ManagerFactory
from redwood_db.user import User

app = summn_web.create_app(__name__)
summn_logging.configure_logging(app.config, debug=app.config.get("DEBUG", False))
summn_web.setup_cors(app)
db = summn_web.create_db(app)
api = summn_web.create_api(app)
summn_web.setup_webargs()
# jwt = summn_web.create_jwt(app)
# jwt.load_user = jwt.default_load_user_fn(db.session, User)
manager_factory = ManagerFactory(db.session, app.config)


class LoggedInSim(object):
    def __init__(self, session):
        self.session = session

    def requires_auth(self, f):
        @wraps(f)
        def decorator(*args, **kwargs):
            user = self.session.query(User).first()
            if user:
                g.user = user
            else:
                raise Exception("No user in database to set as 'logged in'")
            return f(*args, **kwargs)

        return decorator

jwt = LoggedInSim(db.session)

from . import routes
routes.add_routes(api)
