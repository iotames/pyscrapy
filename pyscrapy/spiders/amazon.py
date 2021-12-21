from scrapy.exceptions import UsageError
from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.amazon_goods_list import GoodsRankingList, GoodsListInStore
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.grabs.amazon_goods_reviews import AmazonGoodsReviews
from pyscrapy.extracts.amazon import Common as XAmazon, GoodsReviews as XGoodsReviews
from pyscrapy.models import SiteMerchant, Goods, RankingGoods
from pyscrapy.items import AmazonGoodsItem
from pyscrapy.enum.amazon import EnumGoodsRanking
from pyscrapy.enum.spider import *


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

    stores_urls = [
        {
            'store_name': 'Smallshow',
            'urls': [
                # '/stores/page/7420E66C-9249-44EB-801D-F05D099D35BF',  # Maternity clothes 18
                # '/stores/page/7B493245-46E9-445A-AB79-19909EE30490',  # Maternity shirts 13 OK
                # '/stores/page/C9FAB35C-A576-421D-9198-799B642FBD43',  # Maternity Tank Tops 2
                # '/stores/page/15BD121B-D100-442B-AD3D-9D23ADD406DE',  # Maternity dress 2
                # '/stores/page/38DD04F9-2634-4EFB-81FF-D12931D4E19A',  # Maternity Shorts 1

                # '/stores/page/757B7B48-49DA-492B-98B2-832A0F875B0B',  # Nursing Clothes 52 OK
                # '/stores/page/ADE24067-5927-45F4-B988-80552C16CF90',  # Nursing Shirts 28 OK
                # '/stores/page/8E67FA87-D57F-475D-9B67-E7A80776EC28',  # Nursing Sweatshirt/hoodie 8 OK
                # '/stores/page/FA287B95-D080-4F8B-ADEA-63AD26C6CE06',  # Nursing Dress 14 OK
                # '/stores/page/63EEAE9F-71D4-4944-8867-DC186B1EDA0E'  # Nursing Tank Tops 7 OK
            ]
        }
        # {'store_name': 'Baleaf', 'urls': ['/stores/page/105CBE98-4967-4033-8601-F8B84867E767']},
        # {'store_name': 'sponeed', 'urls': [
        # 7个网页中6个有反爬。 需要从XHR网络请求中抓取ASINList
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
    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST_STORE_PAGE:
            category_name = 'Nursing'  # Nursing Maternity
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
                        meta=dict(merchant_id=store_model.id, category_name=category_name)
                    )
        if self.spider_child == CHILD_GOODS_LIST_RANKING:
            category_name = "Women's Sports Clothing"
            url = '/Best-Sellers-Women/zgbs/sporting-goods/11444119011'
            log_id = 0
            self.ranking_log = self.get_ranking_log(category_name, EnumGoodsRanking.TYPE_BESTSELLERS, log_id=log_id)
            page = 1
            self.url_params['pg'] = str(page)
            yield Request(
                self.get_site_url("{}?{}".format(url, urlencode(self.url_params))),
                callback=GoodsRankingList.parse,
                headers=dict(referer=self.base_url),
                meta=dict(page=page)
            )
        if self.spider_child == CHILD_GOODS_REVIEWS:
            asin = "B093GZ8797"
            goods_url = XAmazon.get_url_by_code(asin, self.url_params)
            reviews_url = XGoodsReviews.get_reviews_url_by_asin(asin)
            goods_model = Goods.get_model(self.db_session, {'code': asin, 'site_id': self.site_id})
            if not goods_model:
                raise RuntimeError("ASIN {} : 商品不存在， 请先通过ASIN采集商品详情".format(asin))
            yield Request(
                reviews_url,
                callback=AmazonGoodsReviews.parse,
                headers=dict(referer=goods_url),
                meta=dict(goods_code=asin, goods_id=goods_model.id, spider=self)
            )
        if self.spider_child == CHILD_GOODS_REVIEWS_BY_RANKING:
            category_name = "Women's Sports Clothing"
            ranking_log = self.get_ranking_log_real(category_name, EnumGoodsRanking.TYPE_BESTSELLERS)
            db_session = RankingGoods.get_db_session()
            ranking_goods_list = RankingGoods.get_all_model(db_session, {'ranking_log_id': ranking_log.id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model = Goods.get_model(db_session, {'id': xgd.goods_id})
                reviews_url = XGoodsReviews.get_reviews_url_by_asin(model.code)
                yield Request(
                    reviews_url,
                    callback=AmazonGoodsReviews.parse,
                    headers=dict(referer=model.url),
                    meta=dict(goods_code=model.code, goods_id=model.id, spider=self)
                )

        if self.spider_child == CHILD_GOODS_LIST_ASIN:
            # store_name = 'Smallshow'
            # store_find = {'name': store_name, 'site_id': self.site_id}
            # store_model = self.db_session.query(SiteMerchant).filter_by(**store_find).first()
            # merchant_id = store_model.id
            merchant_id = 0
            # 手动填写 asin_list [ASIN列表通过mitmproxy中间代理人抓取, 注意缓存后可能会不再走网络请求而是直接读取缓存]
            self.asin_list = [
                {'category_name': 'unknown', 'items': ['B089DJBKN4', 'B093GZ8797']}
            ]
            # self.asin_list = [self.asin_list[-1]]
            for group in self.asin_list:
                category_name = group['category_name']
                for asin in group['items']:
                    item = AmazonGoodsItem()
                    item['merchant_id'] = merchant_id
                    item['asin'] = asin
                    item['code'] = asin
                    item['category_name'] = category_name
                    yield Request(
                        XAmazon.get_url_by_code(asin, self.url_params),
                        callback=AmazonGoodsDetail.parse,
                        # dont_filter=True,
                        meta=dict(item=item)
                    )
        if self.spider_child == CHILD_GOODS_LIST_ALL_COLORS:
            self.goods_model_list = Goods.get_all_model(self.db_session, {'site_id': self.site_id})
            asin_list = []
            for goods_model in self.goods_model_list:
                asin = goods_model.asin
                if asin not in asin_list:
                    asin_list.append(asin)
                    url = XAmazon.get_url_by_code(asin, self.url_params)
                    yield Request(url, callback=AmazonGoodsDetail.parse, headers=dict(referer=self.base_url),
                                  meta=dict(spider=self, goods_model=goods_model))
