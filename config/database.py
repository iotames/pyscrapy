from .baseconfig import BaseConfig


class Database(BaseConfig):
    name = 'database'

    DEFAULT_CONFIG = {
        "host": "127.0.0.1",
        "port": 3306,
        "username": "root",
        "password": "123456",
        "db_name": "pywebspider",
        "db_type": "mysql",  # sqlite
        "db_driver": "pymysql"
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG
