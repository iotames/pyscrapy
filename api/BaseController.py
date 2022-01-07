from service.DB import DB
from Config import Config
import time


class BaseController(object):

    db_session = None

    def __init__(self):
        db = DB.get_instance(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

    @staticmethod
    def f_time(timestamp, fstr="%Y-%m-%d %H:%M"):
        return time.strftime(fstr, time.localtime(timestamp))
