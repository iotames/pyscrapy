import scrapy
from scrapy.http import TextResponse
from ..helpers import Logger
from Config import Config
from ..database import Database
# from sqlalchemy import and_, or_


class BaseSpider(scrapy.Spider):

    name: str
    start_urls = []
    db_session = None
    site_id: int

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name=name, **kwargs)
        self.domain = self.name + '.com'
        self.base_url = "https://www." + self.domain
        self.allowed_domains = [self.domain]

        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

        # if 'spider_child' not in kwargs:
        #     raise SystemExit('lost param spider_child')

        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)

    def parse(self, response: TextResponse, **kwargs):
        pass
