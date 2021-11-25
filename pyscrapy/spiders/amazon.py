from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import AmazonGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
import re
from pyscrapy.grabs.amazon_goods_list import GoodsRankingList as GrabGoodsList
# from translate import Translator


class AmazonSpider(BaseSpider):

    name = 'amazon'
    base_url = "https://www.amazon.com"

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # default 8
        'CONCURRENT_REQUESTS': 8,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    url_params = {
        "language": 'zh_CN'
    }

    top_goods_urls = [
        '/Best-Sellers-Womens-Activewear-Skirts-Skorts/zgbs/fashion/23575633011?{}'
        # '/bestsellers/sporting-goods/706814011?{}'  # 户外休闲销售排行榜
    ]

    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        # self.allowed_domains.append("api.bazaarvoice.com")

    def start_requests(self):
        for url in self.top_goods_urls:
            self.url_params['pg'] = "1"
            url = self.base_url + url.format(urlencode(self.url_params))
            yield Request(
                url,
                callback=GrabGoodsList.parse,
                headers=dict(referer=self.base_url),
                meta=dict(page=1)
            )

