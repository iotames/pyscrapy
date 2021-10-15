import os
import json


class BaseConfig:
    name: str
    file_ext = '.json'
    CONFIG_DIR_PATH = os.path.dirname(__file__)
    filepath: str

    DEFAULT_CONFIG = {}
    SAMPLE_CONFIG = {}

    def __init__(self):
        self.filepath = self.CONFIG_DIR_PATH + os.sep + self.name + self.file_ext

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

    def create_config_file(self):
        if os.path.isfile(self.filepath):
            raise RuntimeError('config file: ' + self.filepath + ' already exists!')
        file_stream = open(self.filepath, 'w', encoding='utf-8')
        json.dump(self.SAMPLE_CONFIG, file_stream, ensure_ascii=False)
