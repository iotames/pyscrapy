from scrapy.exceptions import UsageError
from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.amazon_goods_list import GoodsRankingList, GoodsListInStore
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.grabs.amazon_goods_reviews import AmazonGoodsReviews
from pyscrapy.extracts.amazon import Common as XAmazon, GoodsReviews as XGoodsReviews
from pyscrapy.models import SiteMerchant


class AmazonSpider(BaseSpider):

    name = 'amazon'
    base_url = XAmazon.BASE_URL

    # handle_httpstatus_list = [404]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    url_params = {
        "language": 'zh_CN'
    }

    top_goods_urls = [
        # '/Best-Sellers-Womens-Activewear-Skirts-Skorts/zgbs/fashion/23575633011?{}'
        '/bestsellers/fashion/10208103011?{}'  # 骑行短裤
        # '/bestsellers/sporting-goods/706814011?{}'  # 户外休闲销售排行榜
    ]

    stores_urls = [
        {'store_name': 'Baleaf', 'urls': ['/stores/page/105CBE98-4967-4033-8601-F8B84867E767']},
        # {'store_name': 'sponeed', 'urls': [
        #     '/stores/page/FB3810D0-2453-447E-86C3-45C094E7F3A0',
        #     '/stores/page/65B90D63-5A93-422C-81F5-CD4297B1B65D',
        #     '/stores/page/20758B24-570B-4AB8-B53E-6FD5DC9E8514',
        #     '/stores/page/F36A4167-83B4-45CE-8C08-4F176153083D',
        #     '/stores/page/FBBC92DD-D089-4156-899F-45B69C58F989',
        #     '/stores/page/531253C5-D835-4521-8526-A0DAC4EF4C89',
        #     '/stores/page/258CD320-5D69-43A6-B30D-06F1AFA70C4D'
        # ]}

    ]

    asin_list = []

    CHILD_GOODS_LIST_STORE_PAGE = 'goods_list_store_page'
    CHILD_GOODS_LIST_RANKING = 'goods_list_ranking'
    CHILD_GOODS_REVIEWS = 'goods_reviews'
    CHILD_GOODS_LIST_ASIN = 'goods_list_asin'

    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST_STORE_PAGE:
            for store in self.stores_urls:
                store_name = store['store_name']
                store_find = {'name': store_name, 'site_id': self.site_id}
                print(store_find)
                store_model = self.db_session.query(SiteMerchant).filter_by(**store_find).first()
                if not store_model:
                    store_model = SiteMerchant(**store_find)
                    self.db_session.add(store_model)
                    self.db_session.commit()
                for url in store['urls']:
                    yield Request(
                        self.get_site_url(url),
                        callback=GoodsListInStore.parse,
                        meta=dict(merchant_id=store_model.id)
                    )
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
            goods_url = XAmazon.get_url_by_code(asin, self.url_params)
            reviews_url = XGoodsReviews.get_reviews_url_by_asin(asin)
            next_request = Request(
                reviews_url,
                callback=AmazonGoodsReviews.parse,
                headers=dict(referer=goods_url),
                meta=dict(goods_code=asin)  # goods_id=goods_id
            )
            yield Request(
                goods_url,
                callback=AmazonGoodsDetail.parse,
                headers=dict(referer=self.base_url),
                meta=dict(next_request=next_request)
            )
        if self.spider_child == self.CHILD_GOODS_LIST_ASIN:
            for asin in self.asin_list:
                # item = AmazonGoodsItem()
                # item['merchant_id'] = mchid
                # item['asin'] = asin
                yield Request(
                    XAmazon.get_url_by_code(asin),
                    callback=GoodsListInStore.parse
                )



