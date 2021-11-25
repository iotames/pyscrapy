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
from pyscrapy.grabs.amazon_goods_list import GoodsRankingList
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.grabs.amazon_goods_reviews import AmazonGoodsReviews
from pyscrapy.extracts.amazon import Goods as XGoods, GoodsReviews as XGoodsReviews
from service.Singleton import Singleton

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
        'CONCURRENT_REQUESTS': 1,  # default 16 recommend 5-8
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

    CHILD_GOODS_LIST_RANKING = 'goods_list_ranking'
    CHILD_GOODS_REVIEWS = 'goods_reviews'

    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        # self.allowed_domains.append("api.bazaarvoice.com")

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST_RANKING:
            for url in self.top_goods_urls:
                self.url_params['pg'] = "1"
                url = self.base_url + url.format(urlencode(self.url_params))
                yield Request(
                    url,
                    callback=GoodsRankingList.parse,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1)
                )
        if self.spider_child == self.CHILD_GOODS_REVIEWS:
            asin = "B08Q82QYSV"
            goods_url = XGoods.get_url_by_code(asin, self.url_params)
            yield Request(
                goods_url,
                callback=AmazonGoodsDetail.parse,
                headers=dict(referer=self.base_url)
            )
            time.sleep(5)
            goods_id = Singleton.get_instance().meta['goods_id']  # KeyError: 'goods_id'
            reviews_url = XGoodsReviews.get_reviews_url_by_asin(asin)
            yield Request(
                reviews_url,
                callback=AmazonGoodsReviews.parse,
                headers=dict(referer=goods_url),
                meta=dict(goods_id=goods_id, asin=asin)
            )


