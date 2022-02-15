from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from service.Singleton import Singleton


class DB(Singleton):
    __db_session = None
    __db_engine = None
    __db_type: str
    __sqlite_file = 'sqlite3.db'
    ROOT_PATH = '/'
    db_config = {}

    def __init__(self, config: dict):
        self.db_config = config
        super(DB, self).__init__(config=config)

    @classmethod
    def get_instance(cls, config: dict):
        return super(DB, cls).get_instance(config=config)

    def get_db_engine_uri(self):
        conf = self.db_config
        self.__db_type = conf['db_type']
        drivers_map = {
            "mysql": "pymysql",
            "sqlite": ""
        }
        db_driver = drivers_map[self.__db_type]
        uri = f"{self.__db_type}+{db_driver}://{conf['username']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['db_name']}"
        if conf['db_type'] == 'sqlite':
            uri = 'sqlite:///' + self.ROOT_PATH + '/' + self.__sqlite_file
            if self.__sqlite_file.startswith('/'):
                uri = 'sqlite:///' + self.__sqlite_file
        return uri

    def get_db_engine(self):
        if self.__db_engine is None:
            uri = self.get_db_engine_uri()
            if self.__db_type == 'sqlite':
                self.__db_engine = create_engine(uri)
            else:
                self.__db_engine = create_engine(uri, pool_size=25, pool_recycle=60)
        return self.__db_engine

    def get_db_session(self):
        if self.__db_session is None:
            engine = self.get_db_engine()
            self.__db_session = sessionmaker(engine)()
        return self.__db_session
