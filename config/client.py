from config.baseconfig import BaseConfig


class Client(BaseConfig):
    name = 'client'

    DEFAULT_CONFIG = {
        "start_url": "http://127.0.0.1:8085/index.html"
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG


if __name__ == '__main__':
    c = Client()
    conf = c.get_config()
    print(conf)
