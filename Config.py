import os
from pyscrapy.helpers import JsonFile


class Config:

    ROOT_PATH = os.path.dirname(__file__)
    file_db = 'config/database.json'

    DEFAULT_CONFIG = {
        "database": {
            "host": "127.0.0.1",
            "port": 3306,
            "username": "root",
            "password": "123456",
            "db_name": "pywebspider",
            "db_type": "sqlite",
            "db_driver": "pymysql"
        }
    }

    def get_database(self) -> dict:
        return self.__get_config_by_json(filepath=self.file_db, key='database')

    def __get_config_by_json(self, filepath, key) -> dict:
        filepath = self.get_abspath(filepath)
        obj = JsonFile(filepath)
        read = obj.read()
        default_config = self.DEFAULT_CONFIG[key]
        # 读取配置文件内容，未配置的选项，则设为默认值.
        default_config.update(read)
        return default_config

    @staticmethod
    def get_abspath(path: str):
        if path.startswith('/'):
            return path
        for disk in ['C:', 'D:', 'E:', 'F:', 'G:', 'H:']:
            if path.startswith(disk):
                return path
        return Config.ROOT_PATH + '/' + path

    @staticmethod
    def get_logs_dir():
        return Config.ROOT_PATH + '/runtime/logs'
