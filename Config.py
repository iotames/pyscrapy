import os
from config import Database as DatabaseConf


class Config:

    ROOT_PATH = os.path.dirname(__file__)
    file_db = 'config/database.json'

    def get_database(self) -> dict:
        return DatabaseConf().get_config()
        # return self.__get_config_by_json(filepath=self.file_db, key='database')

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
