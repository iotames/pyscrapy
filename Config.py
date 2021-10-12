import os


class Config:

    ROOT_PATH = os.path.dirname(__file__)

    @staticmethod
    def get_logs_dir():
        return Config.ROOT_PATH + '/runtime/logs'
