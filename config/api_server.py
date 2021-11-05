from config.baseconfig import BaseConfig
from Config import Config as GlobalConfig
import os


class ApiServer(BaseConfig):
    name = 'api_server'

    DEFAULT_CONFIG = {
        "port": 8085,
        "static_folder": GlobalConfig.ROOT_PATH + os.path.sep + 'static'
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG


if __name__ == '__main__':
    s = ApiServer()
    conf = s.get_config()
    print(conf)
