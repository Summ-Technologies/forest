import logging

from sqlalchemy.orm import Session

from redwood_db.user import User

from .google_api import GoogleApiClient
from .google_auth import GoogleAuthClient

logger = logging.getLogger(__name__)


class AutotrophManager(object):

    session: Session = None
    config: dict = None

    # Clients
    google_auth_client: GoogleAuthClient = None
    google_api_client: GoogleApiClient = None

    def __init__(self, session: Session, config: dict = {}):
        self.session = session
        self.config = config

    def _google_auth_client(self):
        if self.google_auth_client == None:
            self.google_auth_client = GoogleAuthClient(self.config)
        return self.google_auth_client

    def _google_api_client(self):
        if self.google_api_client == None:
            self.google_api_client = GoogleApiClient(self.config)
        return self.google_auth_client

    def get_authorization_url(self, user: User):
        pass

    def commit_changes(self):
        self.session.commit()
