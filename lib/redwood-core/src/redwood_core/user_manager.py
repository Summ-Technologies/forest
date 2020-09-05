import logging
from typing import Dict, Optional

import bcrypt

from autotroph_core.google_api import GoogleApiClient
from autotroph_core.google_auth import GoogleAuthClient
from redwood_db.auth import GoogleAuthCredential, GoogleAuthState
from redwood_db.user import User

from .factory import ManagerFactory

logger = logging.getLogger(__name__)


class UserManager(ManagerFactory):
    PW_SALT = bcrypt.gensalt(rounds=12)

    google_api_clients: Dict[str, GoogleApiClient] = {}

    def get_google_account_email(self, user: User) -> Optional[str]:
        """Return email associated with the google account connected to the given user"""
        google_api_client = self._get_google_api_client(user)
        if google_api_client:
            return google_api_client.get_user_profile().get("emailAddress")

    def google_oauth_step1(self, user: User) -> str:
        """Step 1 when linking Redwood account with google account.

        Starts the google account linking process by first generating an oauth URL for
        the user to log in to google with. This function also adds a GoogleAuthState 
        record to the connected database. This record is required to complete the
        oauth flow.

        Args:
            user (User): User who is attempting to link google account

        Returns:
            str: url where user can authenticate with Google account
        """
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        auth_url, auth_state = google_auth_client.get_google_auth_url()
        google_auth_state = GoogleAuthState()
        google_auth_state.state = auth_state
        google_auth_state.user_id = user.id
        self.session.add(google_auth_state)
        self.session.flush()
        return auth_url

    def google_oauth_callback(self, user: User, callback_url: str) -> None:
        """Saves google credentials for linked account.

        Args:
            user (User): Redwood user linking account
            callback_url (str): full url of callback from google
                contains the auth code that can be used to retrieve google credentials
        """
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        google_auth_state: GoogleAuthState = self.session.query(
            GoogleAuthState
        ).order_by(GoogleAuthState.created_at.desc()).filter(
            GoogleAuthState.created_at != None
        ).first()
        google_auth_credentials = google_auth_client.validate_google_auth(
            callback_url, google_auth_state.state
        )
        google_credential = GoogleAuthCredential()
        google_credential.credentials = google_auth_credentials.to_json()
        google_credential.user_id = user.id
        self.session.add(google_credential)
        self.session.flush()

    def authenicate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.

        Args:
            email (str): email
            password (str): password, plaintext

        Returns:
            Optional[User]: User object if successful, None if not
        """
        user = self.session.query(User).filter_by(email=email.lower()).one_or_none()
        if user is not None and self._check_pw(password, user.password_hash):
            return user

    def _get_google_api_client(self, user: User) -> Optional[GoogleApiClient]:
        """Create GoogleApiClient object for given user if they have connected their google account"""
        credentials_record: GoogleAuthCredential = self.session.query(
            GoogleAuthCredential
        ).filter_by(user_id=user.id).order_by(
            GoogleAuthCredential.created_at.desc()
        ).filter(
            GoogleAuthCredential.created_at != None
        ).first()
        if credentials_record:
            credentials_json_str = credentials_record.credentials
            return GoogleApiClient.init_api_client(credentials_json_str)
        else:
            logger.info(
                f"{user} has not connected Google account so cannot initialize a GoogleApiClient instance."
            )
            return

    def _encrypt_pw(self, password: str) -> str:
        """Generate salted password hash"""
        hashed = bcrypt.hashpw(str(password).encode("utf-8"), self.PW_SALT)
        return hashed.decode("utf-8")

    def _check_pw(self, password: str, password_hash: str) -> bool:
        """Check that password and password_hash match"""
        _password = password.encode("utf-8")
        _password_hash = password_hash.encode("utf-8")
        return bcrypt.checkpw(_password, _password_hash)
