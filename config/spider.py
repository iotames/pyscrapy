from config.baseconfig import BaseConfig
from config import HttpProxy, UserAgent
import os


class Spider(BaseConfig):
    name = 'spider'

    components_map = {
        UserAgent.name: UserAgent,
        HttpProxy.name: HttpProxy
    }

    ENV_PRODUCTION = 'production'
    ENV_DEVELOP = 'develop'

    DEFAULT_CONFIG = {
        'env': ENV_PRODUCTION,
        'enabled_components_list': []
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG

    def __init__(self):
        super().__init__()
        if not os.path.isfile(self.filepath):
            self.create_config_file()
        self.enabled_components_name_list = self.get_config()['enabled_components_list']


if __name__ == '__main__':
    spider = Spider()
    print(spider.get_component(UserAgent.name))
    print(spider.get_component(HttpProxy.name))
    print(spider.get_config().get("env"))
