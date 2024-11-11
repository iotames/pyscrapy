from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from service.Singleton import Singleton
from .Config import Config
import os

class DB(Singleton):


    __db_session = None
    __db_engine = None
    __db_type: str
    __sqlite_file = 'sqlite3.db'
    __root_path: str
    db_config = {}

    def __init__(self, config: dict):
        self.db_config = config
        self.__db_type = self.db_config['db_type']
        self.__root_path = Config.get_instance().get_root_path()
        super(DB, self).__init__(config=config)

    def get_db_engine_uri(self):
        conf = self.db_config
        drivers_map = {
            "mysql": "pymysql",
            "postgresql": "psycopg2",
            "sqlite": ""
        }
        db_driver = drivers_map[self.__db_type]
        uri = ""
        if self.__db_type == 'sqlite':
            uri = 'sqlite:///' + self.__root_path + os.path.sep + self.__sqlite_file
            if self.__sqlite_file.startswith('/'):
                uri = 'sqlite:///' + self.__sqlite_file
        else:
            uri = f"{self.__db_type}+{db_driver}://{conf['username']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['db_name']}"
        # engine = create_engine('sqlite:///foo.db')
        # engine = create_engine('sqlite:absolute/path/to/foo.db')
        print(uri)
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
