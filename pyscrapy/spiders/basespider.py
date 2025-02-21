from scrapy import Spider
#import time
from service import DB, Logger
from models import Site

# from sqlalchemy import and_, or_
# from scrapy import Request


class BaseSpider(Spider):

    image_referer = None
    page_size: int
    name: str
    domain: str
    base_url: str
    start_urls = []
    db_session = None
    site_id: int
    app_env: str
    lg: Logger

    def parse(self, response, **kwargs):
        pass

    # 该属性cls静态调用 无法继承覆盖。 必须在继承的类中重写
    # custom_settings = {
    #     'IMAGES_STORE': Config.IMAGES_PATH
    # }

    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    CHILD_GOODS_CATEGORIES = 'goods_categories'
    goods_model_list: list
    spider_child = CHILD_GOODS_DETAIL

    def get_site_url(self, url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith("//"):
            return self.base_url.split(":")[0] + ":" + url
        if url.startswith('/'):
            return self.base_url + url
        return self.base_url + '/' + url

    def __init__(self, name=None, **kwargs):
        print("before __init__, self.base_url=", self.base_url)
        super(BaseSpider, self).__init__(name=name, **kwargs)  # assign kwargs to class attr
        print("after __init__, self.base_url=", self.base_url)
        self.lg = Logger.get_instance()
        self.lg.echo_msg = True

        self.image_referer = self.base_url + "/"
        domain = self.base_url.split("//")[1]
        self.domain = domain
        if domain not in self.allowed_domains:
            print(domain, "---not In self.allowed_domains", self.allowed_domains)
            self.allowed_domains.append(domain)

        db = DB.get_instance()
        self.db_session = db.get_db_session()
        imgdir = self.get_images_dirname()

        # 初始化站点信息
        site = self.db_session.query(Site).filter(Site.name == imgdir).first()
        if not site:
            attrs = {
                'name': imgdir,
                'domain': self.domain,
                'home_url': self.base_url,
                'state': True
            }
            try:
                site = Site(**attrs)
                self.db_session.add(site)
                self.db_session.commit()
            except Exception as e:
                print(e)
                raise Exception(e)
        self.site_id = site.id
        print("----------site.id", self.site_id)

    @classmethod
    def get_site_id(cls):
        site = Site.get_one({'name': cls.name})
        if site:
            return site.id
        return None

    def get_images_dirname(self):
        imgdir = self.name
        if imgdir in ["eyda"]:
            imgdir = self.domain.replace(".", "")
        return imgdir

    # set domain base_url
    def set_base_url(self, url: str):
        url_ele_list = url.split("/")
        protocol = url_ele_list[0]  # https:
        full_domain = url_ele_list[2]
        # domain_ele_list = full_domain.split(".")  # www.abc.com
        # self.domain = domain_ele_list[-2] + "." + domain_ele_list[-1]  # abc.com
        self.base_url = "{}//{}".format(protocol, full_domain)
    
    @staticmethod
    def get_text_by_path(nd, xpath: str) -> str:
        ndd = nd.xpath(xpath)
        return ndd.get().strip() if ndd else None
    @staticmethod
    def get_price_by_text(price_text: str) -> float:
        price = 0.0
        # $59.990
        # currency_list = ['€', '$', '£', 'kr']
        if price_text:
            info = price_text.split('$')
            # $20.00 CAD
            if len(info) > 1:
                price = info[1].strip().replace(",", "").replace("CAD", "").strip()
        if price == 0.0:
            # 399 kr
            info = price_text.split("kr")
            if len(info) > 1:
                price = info[0].strip().replace(",", "")
        if price == 0.0:
            info = price_text.split("£")
            if len(info) > 1:
                price = info[1].strip().replace(",", "")
        if price == 0.0:
            info = price_text.split("€")
            if len(info) > 1:
                price = info[1].strip().replace(",", "")
        return float(price)
    
    # @classmethod
    # def get_export_data(cls) -> list:
    #     raise NotImplementedError()
    #     print("get_export_data({})".format(cls.name))
    #     return []

    def closed(self, reason):
        print("============Close Base Spider : " + self.name)
        print(reason)  # finished
        # log_cls = SpiderRunLog
        # res = self.db_session.query(log_cls).filter(log_cls.id == self.log_id).update(update_data)
        # print(res)
        # self.db_session.commit()
