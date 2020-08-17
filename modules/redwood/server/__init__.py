import os

import summn_logging
import summn_web
from redwood_db.user import User

app = summn_web.create_app(__name__)
summn_logging.configure_logging(app.config, debug=app.config.get("DEBUG", False))
summn_web.setup_cors(app)
db = summn_web.create_db(app)
api = summn_web.create_api(app)
summn_web.setup_webargs()
jwt = summn_web.create_jwt(app)
jwt.load_user = jwt.default_load_user_fn(db.session, User)

from . import routes
routes.add_routes(api)
