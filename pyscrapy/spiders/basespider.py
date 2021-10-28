from scrapy import Spider
from scrapy.http import TextResponse
from ..helpers import Logger
from Config import Config
from ..database import Database
from ..models import Site, SpiderRunLog
# from sqlalchemy import and_, or_
import datetime


class BaseSpider(Spider):

    def parse(self, response, **kwargs):
        pass

    name: str
    start_urls = []
    db_session = None
    site_id: int
    log_id: int
    custom_settings = {
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name=name, **kwargs)
        self.domain = self.name + '.com'
        self.base_url = "https://www." + self.domain
        self.allowed_domains = [self.domain]

        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

        site = self.db_session.query(Site).filter(Site.name == self.name).first()
        if not site:
            attrs = {
                'name': self.name,
                'domain': self.domain,
                'home_url': self.base_url
            }
            site = Site(**attrs)
            self.db_session.add(site)
            self.db_session.commit()
        self.site_id = site.id

        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)
        self.mylogger.echo_msg = True

    def add_spider_log(self):
        logattr = {'spider_name': self.name, 'datetime': datetime.datetime.now()}  # time.strftime("%Y%m%d %H:%M:%S")
        if hasattr(self, 'spider_child'):
            logattr['spider_child'] = self.spider_child
        log = SpiderRunLog(**logattr)
        self.db_session.add(log)
        self.db_session.commit()

