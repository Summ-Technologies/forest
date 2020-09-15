import os

import app
import summn_logging
from redwood_core.config import Config

config = Config()
config.from_pyfile(os.environ["APP_CONFIG"])
summn_logging.configure_logging(config, debug=config.get("DEBUG", False))

app.run(config)
