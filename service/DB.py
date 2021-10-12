from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DB:
    __db_session = None
    __db_engine = None
    __sqlite_file = 'sqlite3.db'
    ROOT_PATH = '/'
    db_config = {}

    def __init__(self, config: dict):
        self.db_config = config

    def get_db_engine_uri(self):
        conf = self.db_config
        uri = f"{conf['db_type']}+{conf['db_driver']}://{conf['username']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['db_name']}"
        if conf['db_type'] == 'sqlite':
            uri = 'sqlite:///' + self.ROOT_PATH + '/' + self.__sqlite_file
            if self.__sqlite_file.startswith('/'):
                uri = 'sqlite:///' + self.__sqlite_file
        return uri

    def get_db_engine(self):
        if self.__db_engine is None:
            self.__db_engine = create_engine(self.get_db_engine_uri())
        return self.__db_engine

    def get_db_session(self):
        if self.__db_session is None:
            engine = self.get_db_engine()
            self.__db_session = sessionmaker(engine)()
        return self.__db_session
