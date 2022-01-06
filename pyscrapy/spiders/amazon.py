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

    name = NAME_AMAZON
    base_url = XAmazon.BASE_URL

    # handle_httpstatus_list = [404]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []  # ["http_proxy", "user_agent"]
    }

    url_params = {
        "language": 'zh_CN'
    }

    """
    store_page = {
            'store_name': 'Baleaf',
            'urls_groups': [
                {'url': 'https://www.amazon.com/stores/page/F7EF2EE6-2F83-4189-98C7-FEB28E89B86C',
                 'category_name': 'Women_Tops'},
                {'url': 'https://www.amazon.com/stores/page/FFBE7943-44B0-4051-805D-46D16FABD55C',
                 'category_name': 'Women_Leggings'},
                {'url': 'https://www.amazon.com/stores/page/4C152E1B-3A9F-40A3-A966-317CECE56E18',
                 'category_name': 'Women_Shorts'},
                {'url': 'https://www.amazon.com/stores/page/5D1F0C72-1A7A-46D7-994C-0294839D5E3F',
                 'category_name': 'Women_Skirts'},
            ]
        }
    """

    asin_list = []
    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        self.allowed_domains.append("amazon.de")
        selenium_children = [CHILD_GOODS_LIST_RANKING, CHILD_GOODS_REVIEWS_BY_RANKING]  #
        if self.spider_child in selenium_children:
            self.SELENIUM_ENABLED = True  # 启用 Selenium 中间件

    def get_site_url(self, url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return self.base_url + url
        return self.base_url + '/' + url

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST_STORE_PAGE:
            store_name = self.input_args["store_name"]
            store_find = {'name': store_name, 'site_id': self.site_id}

            store_model = self.db_session.query(SiteMerchant).filter_by(**store_find).first()
            if not store_model:
                store_model = SiteMerchant(**store_find)
                self.db_session.add(store_model)
                self.db_session.commit()

            code = self.input_args["code"]
            self.group_log_id = int(self.input_args['group_log_id']) if 'group_log_id' in self.input_args else 0
            if self.group_log_id == 0:
                self.create_group_log(code)

            url = self.input_args['url']
            if url.find("http") != 0:
                raise UsageError("url必须以 http 开头")
            meta = dict(merchant_id=store_model.id, category_name=code)
            yield Request(url, callback=GoodsListInStore.parse, meta=meta)

        if self.spider_child == CHILD_GOODS_LIST_RANKING:
            # "Women's Sports Dresses"
            category_name = self.input_args["category_name"]
            # '/Best-Sellers-Sports-Outdoors-Dresses/zgbs/sporting-goods/11444135011'
            url = self.input_args['url']
            if url.find("http") != 0:
                raise UsageError("url必须以 http 开头")
            self.set_base_url(url)

            self.ranking_log_id = int(self.input_args['ranking_log_id']) if 'ranking_log_id' in self.input_args else 0

            rank_type = EnumGoodsRanking.TYPE_BESTSELLERS
            if 'rank_type' in self.input_args:
                rank_type = self.input_args['rank_type']

            page = self.input_args['page'] if 'page' in self.input_args else 1  # 第二页采集的时候经常取不到数据

            if self.ranking_log_id == 0:
                self.create_ranking_log(category_name, rank_type)

            self.url_params['pg'] = str(page)
            referer = self.base_url
            start_url = self.get_site_url("{}?{}".format(url, urlencode(self.url_params)))
            if page == 2:
                referer = start_url.replace('pg=2', 'pg=1')
            print('===============before request = ' + start_url)
            yield Request(
                start_url,
                callback=GoodsRankingList.parse,
                headers=dict(referer=referer),
                meta=dict(page=page, spider=self),
                dont_filter=True
            )

        if self.spider_child == CHILD_GOODS_REVIEWS:
            asin = "B093GZ8797"
            goods_url = XAmazon.get_url_by_code(asin, self.url_params)
            reviews_url = XGoodsReviews(self).get_reviews_url_by_asin(asin)
            goods_model = Goods.get_model(self.db_session, {'code': asin, 'site_id': self.site_id})
            if not goods_model:
                raise RuntimeError("ASIN {} : 商品不存在， 请先通过ASIN采集商品详情".format(asin))
            yield Request(
                reviews_url,
                callback=AmazonGoodsReviews.parse,
                headers=dict(referer=goods_url),
                meta=dict(goods_code=asin, goods_id=goods_model.id, spider=self)
            )

        if self.spider_child == CHILD_GOODS_DETAIL_RANKING:
            if 'ranking_log_id' not in self.input_args:
                raise RuntimeError("缺少ranking_log_id参数")
            self.ranking_log_id = int(self.input_args['ranking_log_id'])
            ranking_goods_list = RankingGoods.get_all_model(self.db_session, {'ranking_log_id': self.ranking_log_id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model: Goods = Goods.get_model(self.db_session, {'id': xgd.goods_id})
                self.set_base_url(model.url)
                self.image_referer = self.base_url + "/"
                goods_item = AmazonGoodsItem()
                goods_item["title"] = model.title
                goods_item["reviews_num"] = model.reviews_num
                goods_item["model"] = model
                yield Request(model.url, callback=AmazonGoodsDetail.parse, meta=dict(item=goods_item), dont_filter=True)

        if self.spider_child == CHILD_GOODS_REVIEWS_BY_RANKING:
            if 'ranking_log_id' not in self.input_args:
                raise RuntimeError("缺少ranking_log_id参数")
            self.ranking_log_id = int(self.input_args['ranking_log_id'])
            ranking_goods_list = RankingGoods.get_all_model(self.db_session, {'ranking_log_id': self.ranking_log_id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model: Goods = Goods.get_model(self.db_session, {'id': xgd.goods_id})
                self.set_base_url(model.url)
                x_reviews = XGoodsReviews(self)
                reviews_url = x_reviews.get_reviews_url_by_asin(model.code)
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
