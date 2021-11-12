from scrapy import Spider
from scrapy.http import TextResponse
from ..helpers import Logger
from Config import Config
from ..database import Database
from ..models import Site, SpiderRunLog
# from sqlalchemy import and_, or_
import datetime
from config.spider import Spider as SpiderConfig


class BaseSpider(Spider):

    def parse(self, response, **kwargs):
        pass

    name: str
    start_urls = []
    db_session = None
    site_id: int
    log_id: int
    app_env: str
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

        # 初始化站点信息
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

        spider_config = SpiderConfig()
        self.app_env = spider_config.get_config().get("env")

        # 检查是否传入 log_id 参数
        self.log_id = 0
        if 'log_id' in kwargs and kwargs['log_id']:
            self.log_id = int(kwargs['log_id'])
        self.log_id = self.add_spider_log(self.log_id)

        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)
        self.mylogger.echo_msg = True

    def add_spider_log(self, log_id=None) -> int:
        if self.app_env == SpiderConfig.ENV_DEVELOP:
            return 0
        now_datetime = datetime.datetime.now()
        logattr = {'spider_name': self.name, 'datetime': now_datetime}  # time.strftime("%Y%m%d %H:%M:%S")
        if hasattr(self, 'spider_child'):
            logattr['spider_child'] = self.spider_child
        log = self.db_session.query(SpiderRunLog).filter(SpiderRunLog.id == log_id).first()
        if log:
            log.datetime = now_datetime
        else:
            logattr["status"] = SpiderRunLog.STATUS_RUNNING
            log = SpiderRunLog(**logattr)
            self.db_session.add(log)
        self.db_session.commit()
        self.log_id = log.id
        return self.log_id

    def closed(self, reason):
        print("============Close Spider : " + self.name)
        print(reason)  # finished
        print(self.log_id)
        if self.app_env == SpiderConfig.ENV_DEVELOP:
            return True
        log_cls = SpiderRunLog
        res = self.db_session.query(log_cls).filter(log_cls.id == self.log_id).update({"status": log_cls.STATUS_DONE})
        print(res)
        self.db_session.commit()
