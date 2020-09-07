import os

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

# Google auth
GOOGLE_OAUTH_SECRETS_FILE = os.environ.get("GOOGLE_OAUTH_SECRETS_FILE")
GOOGLE_OAUTH_CALLBACK_URL = os.environ.get("GOOGLE_OAUTH_CALLBACK_URL")

# Logging
tmp = os.environ.get("SUMM_LOG_FILE")
if tmp:
    SUMM_LOG_FILE = tmp

tmp = os.environ.get("SUMM_LOG_FILE_SIZE")
if tmp:
    SUMM_LOG_FILE_SIZE = tmp

# RMQ connection config
RMQ_USER = os.environ["RMQ_USER"]
RMQ_PASSWORD = os.environ["RMQ_PASSWORD"]
RMQ_HOST = os.environ["RMQ_HOST"]
RMQ_PORT = os.environ["RMQ_PORT"]
