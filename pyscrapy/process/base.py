from pyscrapy.database import Database
from sqlalchemy.orm.session import Session
from Config import Config


class Base:

    db_session: Session

    def __init__(self):
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
