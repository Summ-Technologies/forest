import logging
from typing import Dict, List, Optional, Tuple

import bcrypt
from psycopg2.errorcodes import FOREIGN_KEY_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import IntegrityError

from autotroph_core.google_api import GoogleApiClient
from autotroph_core.google_auth import GoogleAuthClient
from redwood_db.content import Subscription
from redwood_db.google import GoogleAuthCredential, GoogleAuthState, GoogleHistoryId
from redwood_db.user import User, UserConfig, UserSubscription

from .factory import ManagerFactory
from .outcome_codes import OutcomeCodes

logger = logging.getLogger(__name__)


class UserManager(ManagerFactory):
    PW_SALT = bcrypt.gensalt(rounds=12)

    def get_users_with_gmail_permissions(self) -> List[User]:
        user_ids_with_credentials = map(
            lambda id_tuples: id_tuples[0],
            self.session.query(GoogleAuthCredential.user_id).all(),
        )
        return (
            self.session.query(User)
            .filter(User.id.in_(user_ids_with_credentials))
            .all()
        )

    def create_user(
        self, email: str, first_name: str, last_name: str
    ) -> Optional[User]:
        """Creates new user and their initial set of boxes"""
        new_user = User()
        new_user.email = email
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.password_hash = "NO WHITTLE PASSWORDS FOR NOW"
        self.session.add(new_user)
        self.session.flush()
        triage_manager = self.get_manager("triage")
        triage_manager.create_box_for_user(new_user, "Inbox")
        triage_manager.create_box_for_user(new_user, "Queue")
        triage_manager.create_box_for_user(new_user, "Library")
        return new_user

    def add_user_subscription(
        self, user: User, subscription: Subscription
    ) -> Optional[UserSubscription]:
        if (
            self.session.query(UserSubscription)
            .filter_by(user_id=user.id, subscription_id=subscription.id, is_active=True)
            .first()
            is None
        ):
            user_subscription = UserSubscription()
            user_subscription.user_id = user.id
            user_subscription.subscription_id = subscription.id
            user_subscription.is_active = True
            self.session.add(user_subscription)
            self.session.flush()
            return user_subscription

    def get_latest_history_id(self, user: User) -> Optional[str]:
        history_id_record = (
            self.session.query(GoogleHistoryId)
            .order_by(GoogleHistoryId.created_at.desc())
            .filter_by(user_id=user.id)
            .first()
        )
        if history_id_record:
            return history_id_record.history_id

    def create_history_id(self, user: User, current_history_id: str) -> GoogleHistoryId:
        new_history_id = GoogleHistoryId()
        new_history_id.history_id = current_history_id
        new_history_id.user_id = user.id
        self.session.add(new_history_id)
        self.session.flush()
        return new_history_id

    def get_google_account_email(self, user: User) -> Optional[str]:
        """Return email associated with the google account connected to the given user"""
        gmail_api_client = self.get_gmail_api_client(user)
        if gmail_api_client:
            return gmail_api_client.get_user_profile().get("emailAddress")

    def google_login_step1(self) -> str:
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        auth_url, auth_state = google_auth_client.get_google_login_url()
        return auth_url

    def google_login_callback(self, callback_url: str) -> Optional[User]:
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        google_email_address = google_auth_client.validate_google_login(callback_url)
        return (
            self.session.query(User).filter_by(email=google_email_address).one_or_none()
        )

    def google_signup_step1(self, gmail_permissions=False) -> str:
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        auth_url, auth_state = google_auth_client.get_google_signup_url()
        return auth_url

    def google_signup_callback(
        self, callback_url: str
    ) -> Tuple[Optional[User], OutcomeCodes]:
        """TODO add whitelist and error codes for different reasons signup failed"""
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        (
            google_email_address,
            first_name,
            last_name,
        ) = google_auth_client.validate_google_signup(callback_url)
        if google_email_address:  # TODO add whitelist here
            try:
                new_user = self.create_user(google_email_address, first_name, last_name)
                return (new_user, OutcomeCodes.SUCCESS)
            except IntegrityError as e:
                self.session.rollback()
                if e.orig.pgcode == UNIQUE_VIOLATION:
                    logger.info(
                        f"Account already exists for email: {google_email_address}"
                    )
                    return (
                        (
                            self.session.query(User)
                            .filter_by(email=google_email_address)
                            .one_or_none()
                        ),
                        OutcomeCodes.ERROR_SIGNUP_USER_ALREADY_EXISTS,
                    )
                else:
                    raise e
        else:
            return (None, OutcomeCodes.ERROR_SIGNUP_USER_NOT_WHITELISTED)
        return (None, OutcomeCodes.ERROR)

    def gmail_permissions_step1(self, user: User) -> str:
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
        auth_url, auth_state = google_auth_client.get_gmail_auth_url()
        google_auth_state = GoogleAuthState()
        google_auth_state.state = auth_state
        google_auth_state.user_id = user.id
        self.session.add(google_auth_state)
        self.session.flush()
        return auth_url

    def gmail_auth_callback(self, user: User, callback_url: str) -> None:
        """Saves google credentials for linked account.

        Args:
            user (User): Redwood user linking account
            callback_url (str): full url of callback from google
                contains the auth code that can be used to retrieve google credentials
        """
        google_auth_client: GoogleAuthClient = GoogleAuthClient(self.config)
        google_auth_state: GoogleAuthState = (
            self.session.query(GoogleAuthState)
            .order_by(GoogleAuthState.created_at.desc())
            .filter(GoogleAuthState.created_at != None)
            .first()
        )
        google_auth_credentials = google_auth_client.validate_gmail_auth(
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

    def get_gmail_api_client(self, user: User) -> Optional[GoogleApiClient]:
        """Create GoogleApiClient object for given user if they have connected their google account"""
        credentials_record: GoogleAuthCredential = (
            self.session.query(GoogleAuthCredential)
            .filter_by(user_id=user.id)
            .order_by(GoogleAuthCredential.created_at.desc())
            .filter(GoogleAuthCredential.created_at != None)
            .first()
        )
        if credentials_record:
            credentials_json_str = credentials_record.credentials
            return GoogleApiClient.init_api_client(credentials_json_str)
        else:
            logger.info(
                f"{user} has not connected Google account so cannot initialize a GoogleApiClient instance."
            )
            return

    def get_user_config(self, user: User) -> Tuple[UserConfig, bool]:
        """Get's user's config object (and creates one if it doesn't exist)
        Returns:
            [user_config: UserConfig, new_config: bool] where new_config
                is true when the object returned was newly created
        """
        new_config = False
        config = self.session.query(UserConfig).filter_by(user_id=user.id).one_or_none()
        if not config:
            logger.debug(
                f"Config record doesn't exist for {user}. Creating default config..."
            )
            new_config = True
            config = UserConfig()
            config.user_id = user.id
            self.session.add(config)
            self.session.flush()
        return (config, new_config)

    def _encrypt_pw(self, password: str) -> str:
        """Generate salted password hash"""
        hashed = bcrypt.hashpw(str(password).encode("utf-8"), self.PW_SALT)
        return hashed.decode("utf-8")

    def _check_pw(self, password: str, password_hash: str) -> bool:
        """Check that password and password_hash match"""
        _password = password.encode("utf-8")
        _password_hash = password_hash.encode("utf-8")
        return bcrypt.checkpw(_password, _password_hash)
