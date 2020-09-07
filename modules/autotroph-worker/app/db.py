from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def setup_db_session(db_uri: str):
    db_engine = create_engine(db_uri)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    return session
