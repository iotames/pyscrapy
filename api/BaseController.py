from pyscrapy.database import Database
from Config import Config


class BaseController(object):

    db_session = None

    def __init__(self):
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
