from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.shein_goods_list import GoodsList
from pyscrapy.grabs.shein_goods import GoodsDetail
from pyscrapy.models import Goods
from pyscrapy.extracts.shein import BASE_URL


class SheinSpider(BaseSpider):
    """
    us.shein.com 电商平台
    """

    name = 'shein'
    base_url = BASE_URL

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'LOG_LEVEL': 'WARNING',
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': False,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 8,  # default 8
        # 'CONCURRENT_REQUESTS': 16,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    url_params = {
        'sort': 7  # ?sort=7 top reviews
    }

    top_goods_urls = [
        '/category/Active-sc-00856973.html'  # 女装运动服
    ]

    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_REVIEWS = 'goods_reviews'

    def __init__(self, name=None, **kwargs):
        super(SheinSpider, self).__init__(name=name, **kwargs)
        self.base_url = BASE_URL

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for url in self.top_goods_urls:
                url = "{}{}?{}".format(self.base_url, url, urlencode(self.url_params))
                yield Request(
                    url,
                    callback=GoodsList.parse,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1)
                )
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            self.goods_model_list = self.db_session.query(Goods).filter(
                Goods.site_id == self.site_id
            ).all()
            for model in self.goods_model_list:
                yield Request(
                    model.url,
                    callback=GoodsDetail.parse,
                    headers=dict(referer=self.base_url)
                )

