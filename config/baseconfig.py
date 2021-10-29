import os
import json
import random


class BaseConfig:
    name: str
    file_ext = '.json'
    CONFIG_DIR_PATH = os.path.dirname(__file__)
    filepath: str
    config: dict

    DEFAULT_CONFIG = {}
    SAMPLE_CONFIG = {}
    enabled_components_name_list = []
    components_map = {}

    def __init__(self):
        self.filepath = self.CONFIG_DIR_PATH + os.sep + self.name + self.file_ext
        if not os.path.isfile(self.filepath):
            self.create_config_file()
        self.config = self.get_config()

    def get_config_by_json(self) -> dict:
        # 如果文件不存在，则返回空字典
        if not os.path.isfile(self.filepath):
            return {}
        file = open(self.filepath, "r", encoding="utf-8")
        data = json.load(file)
        file.close()
        return data

    def get_config(self) -> dict:
        self.DEFAULT_CONFIG.update(self.get_config_by_json())
        return self.DEFAULT_CONFIG

    def get_items(self) -> list:
        conf = self.get_config()
        return conf['items']

    def choice_one_from_items(self):
        return random.choice(self.get_items())

    def create_config_file(self):
        if os.path.isfile(self.filepath):
            raise RuntimeError('config file: ' + self.filepath + ' already exists!')
        file_stream = open(self.filepath, 'w', encoding='utf-8')
        json.dump(self.DEFAULT_CONFIG, file_stream, ensure_ascii=False)

    def get_component(self, name):
        if name in self.enabled_components_name_list:
            if name not in self.components_map:
                raise AttributeError('dict components_map is not defined key: ' + name)
            return self.components_map[name]()
        return None


if __name__ == '__main__':
    config = BaseConfig()
    print(config.get_component('user_agent'))
