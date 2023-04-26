from scrapy import Spider
import time
from ..helpers import Logger
from Config import Config
from service.DB import DB
from ..models import Site, SpiderRunLog, RankingLog, GroupLog
from scrapy.exceptions import UsageError
import datetime
from config.spider import Spider as SpiderConfig
from pyscrapy.helpers import JsonFile
from pyscrapy.models.Goods import Goods
from sqlalchemy import and_, or_
from scrapy import Request
import hashlib
from scrapy.utils.python import to_bytes


class BaseSpider(Spider):

    SELENIUM_ENABLED = False
    SPLASH_ENABLED = False

    image_referer = None

    @staticmethod
    def cookie_to_dic(cookies) -> dict:
        return JsonFile.cookie_to_dic(cookies)

    def parse(self, response, **kwargs):
        pass

    name: str
    domain: str
    base_url: str
    start_urls = []
    db_session = None
    site_id: int
    log_id: int
    app_env: str
    spider_config: SpiderConfig
    ranking_log_id = 0
    group_log_id = 0
    input_args = {}
    log_status = SpiderRunLog.STATUS_DONE

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

    def get_site_url(self, url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return self.base_url + url
        return self.base_url + '/' + url

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name=name, **kwargs)
        if self.base_url:
            self.domain = self.base_url.split("//")[1]
        else:
            self.domain = self.name + '.com'
            self.base_url = "https://www." + self.domain

        self.image_referer = self.base_url + "/"
        self.allowed_domains = [self.domain]

        # db = Database(Config().get_database())
        db = DB.get_instance(config=Config().get_database())
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

    def request_list_goods_detail(self, get_request=None) -> list:
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            before_time = time.time()
            # if self.app_env == self.spider_config.ENV_PRODUCTION:
            #     before_time = time.time() - (2 * 3600)  # 2小时内的采集过的商品不会再更新
            self.goods_model_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id, or_(
                    Goods.status == Goods.STATUS_UNKNOWN,
                    Goods.updated_at < before_time)
            )).all()
            goods_list_len = len(self.goods_model_list)
            print(f"=======goods_list_len============ : {str(goods_list_len)}")
            if goods_list_len > 0:
                request_list = []
                for model in self.goods_model_list:
                    url = model.url
                    if get_request:
                        url = get_request(model)
                    headers = {'referer': self.image_referer}
                    q = Request(url, self.parse_goods_detail, headers=headers, meta=dict(goods_model=model))
                    request_list.append(q)
                return request_list
            else:
                self.log_status = SpiderRunLog.STATUS_FAIL
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def set_base_url(self, url: str):
        url_ele_list = url.split("/")
        protocol = url_ele_list[0]  # https:
        full_domain = url_ele_list[2]
        domain_ele_list = full_domain.split(".")  # www.abc.com
        self.domain = domain_ele_list[-2] + "." + domain_ele_list[-1]  # abc.com
        self.base_url = "{}//{}".format(protocol, full_domain)

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

    def create_ranking_log(self, category_name="", rank_type=0):
        db_session = self.db_session
        ranking_log = RankingLog.get_log(db_session, self.site_id, category_name, rank_type)
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
            ranking_log = RankingLog(**attrs)
            db_session.add(ranking_log)
            db_session.commit()
            self.ranking_log_id = ranking_log.id

    def create_group_log(self, code: str, args: dict):
        db_session = self.db_session
        log = GroupLog.get_log(db_session, self.site_id, code, args['group_type'])
        if log:
            self.group_log_id = log.id
            # 判断 created_at 来确定是否新建 group_log
            if (time.time() - log.created_at) > 3600 * 12:
                log = None
        if not log:
            now_date = datetime.datetime.now()
            attrs = {
                'site_id': self.site_id,
                'code': code,
                'log_date': now_date
            }
            attrs.update(args)
            log = GroupLog(**attrs)
            db_session.add(log)
            db_session.commit()
            self.group_log_id = log.id

    @staticmethod
    def get_guid_by_url(url: str) -> str:
        print(url)
        return hashlib.sha1(to_bytes(url)).hexdigest()

    def closed(self, reason):
        print("============Close Base Spider : " + self.name)
        print(reason)  # finished
        print(self.log_id)
        if self.app_env == SpiderConfig.ENV_DEVELOPMENT:
            return True
        log_cls = SpiderRunLog
        update_data = {"status": self.log_status}
        if self.ranking_log_id > 0:
            update_data["link_id"] = self.ranking_log_id
        if self.group_log_id > 0:
            update_data["link_id"] = self.group_log_id
        res = self.db_session.query(log_cls).filter(log_cls.id == self.log_id).update(update_data)
        print(res)
        self.db_session.commit()
