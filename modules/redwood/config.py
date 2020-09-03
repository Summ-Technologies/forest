import os

# CORS through summn-web
CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "").split(",")

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

# JWT Auth
SECRET_KEY = os.environ.get("SECRET_KEY")
JWT_LIFESPAN = os.environ.get("JWT_LIFESPAN", -1)
JWT_FRESHSPAN = os.environ.get("JWT_FRESHSPAN", 5)

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
