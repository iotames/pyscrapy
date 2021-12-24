from scrapy import Spider
import time
from ..helpers import Logger
from Config import Config
from ..database import Database
from ..models import Site, SpiderRunLog, RankingLog
from scrapy.exceptions import UsageError
import datetime
from config.spider import Spider as SpiderConfig
from pyscrapy.helpers import JsonFile


class BaseSpider(Spider):

    SELENIUM_ENABLED = False
    SPLASH_ENABLED = False

    @staticmethod
    def cookie_to_dic(cookies) -> dict:
        return JsonFile.cookie_to_dic(cookies)

    def parse(self, response, **kwargs):
        pass

    name: str
    base_url: str
    start_urls = []
    db_session = None
    site_id: int
    log_id: int
    app_env: str
    spider_config: SpiderConfig
    ranking_log_id = 0
    input_args = {}

    # 该属性cls静态调用 无法继承覆盖。 必须在继承的类中重写
    custom_settings = {
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    CHILD_GOODS_CATEGORIES = 'goods_categories'
    goods_model_list: list
    spider_child = CHILD_GOODS_DETAIL

    @classmethod
    def get_site_url(cls, url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return cls.base_url + url
        return cls.base_url + '/' + url

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
        self.spider_config = spider_config

        # 爬虫入参
        if 'input_args' in kwargs:
            self.input_args = kwargs['input_args']

        # 检查是否传入 log_id 参数
        self.log_id = 0
        if 'log_id' in kwargs and kwargs['log_id']:
            self.log_id = int(kwargs['log_id'])
        self.log_id = self.add_spider_log(self.log_id)

        # 初始化mylogger配置
        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)
        self.mylogger.echo_msg = True

        # 校验爬虫子操作
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']

    def add_spider_log(self, log_id=None) -> int:
        if self.app_env == SpiderConfig.ENV_DEVELOPMENT:
            return 0
        now_datetime = datetime.datetime.now()
        logattr = {'spider_name': self.name, 'datetime': now_datetime}  # time.strftime("%Y%m%d %H:%M:%S")
        if hasattr(self, 'spider_child'):
            logattr['spider_child'] = self.spider_child
        log = self.db_session.query(SpiderRunLog).filter(SpiderRunLog.id == log_id).first()
        if log:
            log.datetime = now_datetime
            log.status = SpiderRunLog.STATUS_RUNNING
        else:
            logattr["status"] = SpiderRunLog.STATUS_RUNNING
            log = SpiderRunLog(**logattr)
            self.db_session.add(log)
        self.db_session.commit()
        self.log_id = log.id
        return self.log_id

    def create_ranking_log(self, category_name="", rank_type=0, log_id=0):
        db_session = RankingLog.get_db_session()
        ranking_log = RankingLog.get_log(db_session, self.site_id, category_name, rank_type, log_id=log_id)
        if ranking_log:
            self.ranking_log_id = ranking_log.id
            # 判断 created_at 来确定是否新建 ranking_log
            if (time.time() - ranking_log.created_at) > 3600 * 12:
                ranking_log = None
        if not ranking_log:
            now_date = datetime.datetime.now()
            attrs = {
                'site_id': self.site_id,
                'category_name': category_name,
                'rank_type': rank_type,
                'rank_date': now_date
            }
            db_session = RankingLog.get_db_session()
            ranking_log = RankingLog(**attrs)
            db_session.add(ranking_log)
            db_session.commit()
            self.ranking_log_id = ranking_log.id

    def closed(self, reason):
        print("============Close Base Spider : " + self.name)
        print(reason)  # finished
        print(self.log_id)
        if self.app_env == SpiderConfig.ENV_DEVELOPMENT:
            return True
        log_cls = SpiderRunLog
        update_data = {"status": log_cls.STATUS_DONE}
        if self.ranking_log_id > 0:
            update_data["link_id"] = self.ranking_log_id
        res = self.db_session.query(log_cls).filter(log_cls.id == self.log_id).update(update_data)
        print(res)
        self.db_session.commit()
