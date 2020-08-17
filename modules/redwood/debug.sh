# Run this from the root of the repo and ensure your .env file exists
FLASK_APP=$PWD/modules/redwood/server/ APP_CONFIG=$PWD/modules/redwood/config.py env $(cat .env) flask run
