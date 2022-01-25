from config.baseconfig import BaseConfig


class Translator(BaseConfig):

    name = 'translator'

    PROVIDER_YOUDAO = "youdao"

    DEFAULT_CONFIG = {
        "http_proxy": None,
        "app_provider": PROVIDER_YOUDAO,
        "app_key": "",
        "app_secret": ""
    }

    SAMPLE_CONFIG = DEFAULT_CONFIG


