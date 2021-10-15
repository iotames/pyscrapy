"""
IP代理池
"""
from config.baseconfig import BaseConfig


class HttpProxy(BaseConfig):

    name = 'proxy'

    DEFAULT_CONFIG = {
        'items': []
    }

    SAMPLE_CONFIG = {
        'items': [
            '127.0.0.1:1080',
            '127.0.0.1:1234'
        ]
    }


if __name__ == '__main__':
    HttpProxy().create_config_file()
