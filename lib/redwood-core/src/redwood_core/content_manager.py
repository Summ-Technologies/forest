import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, exists

from autotroph_core.google_api import GoogleApiClient
from redwood_db.content import Article, Subscription
from redwood_db.triage import Box, Triage
from redwood_db.user import User, UserSubscription

from .article import TransformerFactory
from .article import source as source_utils
from .factory import ManagerFactory
from .user_manager import UserManager

logger = logging.getLogger(__name__)


class ContentManager(ManagerFactory):
    """Manages content (like articles)

    Config options available:
        BOX_PAGE_SIZE, number of articles in a single page for a box

    """

    def get_new_emails(self, user: User) -> List[str]:
        """
        Returns message_ids for all emails since history_id.
        If history_id is None then returns all message_ids from the past 2 weeks

        Note, this message adds the current history_id for the given user to the databse
        session so the session does need to be committed after calling this method.
        """
        user_manager = self.get_manager("user")
        gmail_api_client = user_manager.get_gmail_api_client(user)
        history_id = user_manager.get_latest_history_id(user)
        latest_emails, current_history_id = gmail_api_client.get_new_emails(history_id)
        user_manager.create_history_id(user, current_history_id)
        return latest_emails

    def is_email_newsletter(self, user: User, gmail_message_id: str) -> bool:
        """Returns if the gmail message a newsletter that should be imported.

        Args:
            user (User):
            gmail_message_id (str): gmail's id of email

        Returns:
            bool: is email whittle newsletter
        """
        user_manager: UserManager = self.get_manager("user")
        gmail_api_client = user_manager.get_gmail_api_client(user)
        gmail_message = gmail_api_client.get_email(gmail_message_id, format="metadata")
        if gmail_message:
            name, from_address = GoogleApiClient.get_email_from_address(gmail_message)
            for subscription in source_utils.general_newsletter_subscriptions:
                if source_utils.is_newsletter_subscription(
                    from_address.lower() if from_address else from_address,
                    name.lower() if name else name,
                    subscription,
                ):
                    logger.info(
                        f"GmailMessage from name: {name}, address: {from_address} is a generic subscription matching: {subscription}"
                    )
                    return True
            for subscription in self.get_subscriptions_by_user(user):
                if source_utils.is_newsletter_subscription(
                    from_address.lower() if from_address else from_address,
                    name.lower() if name else name,
                    subscription,
                ):
                    logger.info(
                        f"GmailMessage from name: {name}, address: {from_address} is a personal subscription matching: {subscription}"
                    )
                    return True
        return False

    def create_new_article_from_gmail(
        self, user: User, gmail_message: dict
    ) -> Optional[Article]:
        """Retrieves email from gmail and saves data as new article record.

        Args:
            user (User):
            gmail_message_id (str):
            move_to_library (bool): triage to library instead of inbox

        Returns:
            (Article): newly added and flushed article record
        """
        tranformer_factory = TransformerFactory(self.config)
        user_manager = self.get_manager("user")
        gmail_message_id = gmail_message["id"]
        title = GoogleApiClient.get_header_by_name(gmail_message, "Subject")[0]
        from_name, from_address = GoogleApiClient.get_email_from_address(gmail_message)
        source_type = source_utils.source_to_source_type(from_address)
        transformer = tranformer_factory.get_transformer(source_type)
        received_dt = GoogleApiClient.get_email_received_datetime(gmail_message)
        received_dt = received_dt if received_dt else datetime.now(tz=timezone.utc)
        html_body = GoogleApiClient.get_email_html_body(gmail_message)
        if not html_body:
            logger.error(
                f"Can't create article from gmail_message: {gmail_message} because not html body"
            )
        html_content, outline = transformer.get_html_and_outline(html_body)
        text_content = transformer.get_text(html_content)
        ((gmail_message_exists,),) = self.session.query(
            exists().where(
                and_(
                    Article.gmail_message_id == gmail_message_id,
                    Article.user_id == user.id,
                )
            )
        )
        # TODO this logic should be in the is_email_newsletter function, not here
        # Should the message be excluded because of the subject line
        #   For example: substack publishers get emails from the same from_name/from_address as their
        #   actual newsletter, when someone simply subscribes. This will exclude creating an article
        #   for substack addresses with "New signup" in the subjectline
        def do_exclude_by_subjectline(
            from_name: str, from_address: str, title: str
        ) -> bool:
            from_address = "" if from_address is None else from_address.lower()
            from_name = "" if from_name is None else from_name.lower()
            title = "" if title is None else title.lower()
            if "substack" in from_address:
                if "new" in title and "signup" in title:
                    return True
                elif "complete your signup" in title:
                    return True
            return False

        exclude_by_subjectline = do_exclude_by_subjectline(
            from_name, from_address, title
        )

        if gmail_message_exists:
            logger.warning(
                f"{user} attempting to create article from email with id: {gmail_message_id} but this id exists in the articles table already."
            )
        elif exclude_by_subjectline:
            logger.info(
                f"{user} attempting to create article, but was excluded due to subjectline. from_name: {from_name}, from_address: {from_address}, subject: {title}"
            )
        else:
            new_article = self.create_new_article(
                user,
                title,
                from_address,
                author=from_name,
                outline=outline,
                text_content=text_content,
                html_content=html_content,
                gmail_message_id=gmail_message_id,
                received_at=received_dt,
            )
            if new_article:
                triage_manager = self.get_manager("triage")
                box = triage_manager.get_user_inbox(user)
                triage_manager.create_new_triage(new_article, box)
                return new_article

    def create_new_article(
        self,
        user: User,
        title: str,
        source: str,
        author: str,
        outline: str,
        text_content: str,
        html_content: str,
        gmail_message_id: str,
        received_at: datetime,
    ) -> Article:
        """Creates a new article.
        Adds, and flushes, but does not commit the article record.

        Args:
            user (User): user who owns the article
            title (str): title
            source (str): source
            content (str): content
            html_content (str): html_string
        Returns:
            (Article): newly created article record (uncommitted)
        """
        article = Article()
        article.title = title
        article.source = source
        article.author = author
        article.outline = outline
        article.text_content = text_content
        article.html_content = html_content
        article.gmail_message_id = gmail_message_id
        article.user_id = user.id
        article.message_received_at = received_at
        self.session.add(article)
        self.session.flush()
        return article

    def get_article_by_id(self, id, user: User = None) -> Optional[Article]:
        """
        Get article by id. If user is passed, only return an article if the user is the owner of the article.
        Return article if article exists, else None
        """
        article: Optional[Article] = self.session.query(Article).get(id)
        if user:
            if article and article.user_id == user.id:
                return article
            else:
                logger.info(
                    f"{user} tried to retrieve article: {article} but was not the owner."
                )
                return None
        else:
            return article

    def get_articles_by_id(
        self, user: User, box_id: int, article_ids: List[int]
    ) -> List[Article]:
        return (
            self.session.query(Article)
            .filter_by(user_id=user.id)
            .filter(Article.id.in_(article_ids))
            .all()
        )

    def get_num_articles_by_box_id(self, user: User, box_id: int) -> int:
        user_articles = self.session.query(Article.id).filter_by(user_id=user.id)
        article_count = (
            self.session.query(Triage.article_id)
            .filter(Triage.article_id.in_(user_articles))
            .filter_by(box_id=box_id)
            .filter_by(is_active=True)
            .count()
        )
        return article_count

    def get_articles_by_box_id(self, user: User, box_id: int) -> List[int]:
        """Gets the article ids for the given box id and page.

        Args:
            user (User): user requesting articles
            box_id (int): id of box articles in

        Returns:
            List[Article]: list of article resources
        """
        user_articles = self.session.query(Article.id).filter_by(user_id=user.id)
        triage_manager = self.get_manager("triage")
        box = triage_manager.get_box_by_id(box_id)
        if not box:
            return []

        base_query = (
            self.session.query(Triage.article_id)
            .filter(Triage.article_id.in_(user_articles))
            .filter_by(box_id=box_id)
            .filter_by(is_active=True)
        )

        ## TODO change this to an actual value on the box record itself
        if box.name and box.name.lower() == "inbox":
            ## Received at time
            article_ids = (
                self.session.query(Article.id)
                .filter(Article.id.in_(base_query))
                .order_by(Article.message_received_at.desc())
                .all()
            )
        elif box.name and box.name.lower() == "queue":
            ## FIFO
            article_ids = base_query.order_by(Triage.created_at.asc()).all()
        else:  # basically == elif box.name and box.name.lower() == "library":
            ## LIFO
            article_ids = base_query.order_by(Triage.created_at.desc()).all()
        return [article_id for (article_id,) in article_ids]

    def get_articles_by_search_query(self, user: User, box_id: int, query: str):
        user_articles = self.session.query(Article.id).filter_by(user_id=user.id)
        article_ids = (
            self.session.query(Triage.article_id)
            .filter(Triage.article_id.in_(user_articles))
            .filter_by(box_id=box_id)
            .filter_by(is_active=True)
        )

        matching_article_ids = (
            self.session.query(Article.id)
            .filter(Article.id.in_(article_ids))
            .filter(
                Article.title.ilike(f"%{query.lower()}%"),
                Article.text_content.ilike(f"%{query.lower()}%"),
            )
        ).all()
        return [article_id for (article_id,) in matching_article_ids]

    def get_subscriptions_by_user(self, user: User):
        subscription_ids = (
            self.session.query(UserSubscription.subscription_id)
            .filter_by(user_id=user.id, is_active=True)
            .all()
        )
        return (
            self.session.query(Subscription)
            .filter(Subscription.id.in_(subscription_ids))
            .all()
        )

    def get_subscription_by_from_address(
        self, from_address: str
    ) -> Optional[Subscription]:
        """Returns Subscription record for exact match of from_address and any from name"""
        from_address = f"^{from_address}$"  # create exact match record
        from_name = ".*"  # any from name
        return (
            self.session.query(Subscription)
            .filter_by(from_address=from_address, name=from_name)
            .first()
        )

    def create_subscription(self, from_address: str):
        """Creates a Subscription record for exact match of from_address"""
        from_address = f"^{from_address}$"  # create exact match record
        from_name = ".*"  # any from name
        new_subscription = Subscription()
        new_subscription.from_address = from_address
        new_subscription.name = from_name
        self.session.add(new_subscription)
        self.session.flush()
        return new_subscription

    def bookmark_article(self, article: Article) -> Article:
        """Add bookmarked to article"""
        if not article.bookmarked:
            article.bookmarked = True
            self.session.add(article)
            self.session.flush()
        return article

    def unbookmark_article(self, article: Article) -> Article:
        """Remove bookmark from article"""
        if article.bookmarked:
            article.bookmarked = False
            self.session.add(article)
            self.session.flush()
        return article
