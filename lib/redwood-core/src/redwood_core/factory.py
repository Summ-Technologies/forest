import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ManagerFactory(object):

    session: Session = None
    config: dict = None
    manager_mapping = {}

    def __init__(self, session: Session, config: dict = {}):
        self.session = session
        self.config = config
        self.manager_cache = {}

    @classmethod
    def register_manager(cls, manager_name: str, manager_class):
        cls.manager_mapping[manager_name] = manager_class

    def get_manager(self, manager_name: str):
        if self.session is None:
            logger.warning(
                "Can't call get_manager before initializing the ManagerFactory object"
            )
            return
        manager = self.manager_cache.get(manager_name, None)
        if not manager:
            # initialize manager and cache it
            manager_class = self.manager_mapping.get(manager_name)
            if manager_class is None:
                logger.warning(
                    f"Invalid manager name. No corresponding class for name: {manager_name}"
                )
            else:
                manager = manager_class(self.session, self.config)
                self.manager_cache[manager_name] = manager
        return manager

    def commit_changes(self):
        self.session.commit()
