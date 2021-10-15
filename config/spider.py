from config.baseconfig import BaseConfig
from config import HttpProxy, UserAgent
import os


class Spider(BaseConfig):
    name = 'spider'

    proxy: HttpProxy = None
    user_agent: UserAgent = None

    components = {
        UserAgent.name: UserAgent,
        HttpProxy.name: HttpProxy
    }

    DEFAULT_CONFIG = {
        'components_list': []
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG

    def __init__(self):
        super().__init__()
        if not os.path.isfile(self.filepath):
            self.create_config_file()
        for component in self.get_config()['components_list']:
            if not hasattr(self, component):
                raise SyntaxError('component name : ' + component + " is not defined")
            setattr(self, component, self.components[component]())


if __name__ == '__main__':
    spider = Spider()
    print(spider.proxy.get_items())
    print(spider.user_agent.get_items())
    print(spider.get_config())
