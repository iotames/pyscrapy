from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.shein_goods_list import GoodsList
from pyscrapy.grabs.shein_goods import GoodsDetail
from pyscrapy.extracts.shein import BASE_URL
from pyscrapy.models import GoodsCategory, Goods, RankingGoods
from pyscrapy.enum.shein import EnumGoodsRanking
from pyscrapy.enum.spider import *  # CHILD_GOODS_REVIEWS_BY_RANKING


class SheinSpider(BaseSpider):
    """
    us.shein.com 电商平台
    """

    name = 'shein'
    base_url = BASE_URL

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        # 'LOG_LEVEL': 'WARNING',
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
        'page': 1,
        # {"recommend": "", "top reviews": 7, "most popular": 8, "new arrivals": 9, "price low to high": 10, "price high to low": 11}
        'sort': 7
    }

    category_goods_list = [
        {
            'total_page': 40,
            'url': '/category/Active-sc-00856973.html'  # 女装运动服
        }
    ]

    def __init__(self, name=None, **kwargs):
        super(SheinSpider, self).__init__(name=name, **kwargs)
        self.base_url = BASE_URL

    __get_categories_map = {}

    @property
    def categories_map(self):
        if not self.__get_categories_map:
            self.__get_categories_map = self.get_categories_map()
        return self.__get_categories_map

    def get_request_goods_list(self, url, meta: dict):
        headers = None
        page = meta['page'] if 'page' in meta else 0
        if page == 1:
            headers = dict(referer=self.base_url)
        print(url)
        return Request(
            url,
            callback=GoodsList.parse,
            headers=headers,
            meta=meta
        )

    def get_request_goods_detail(self, model: Goods):
        return Request(model.url, callback=GoodsDetail.parse, headers=dict(referer=self.base_url),
                       meta=dict(spider=self, categories_map=self.categories_map, goods_model=model))

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST:
            meta = dict(spider=self, categories_map=self.categories_map)
            for category in self.category_goods_list:
                total_page = category['total_page']
                for page in range(1, (total_page + 1)):
                    url = "{}{}?{}".format(self.base_url, category['url'], urlencode({'page': page, 'sort': 7}))
                    meta['page'] = page
                    yield self.get_request_goods_list(url, meta)

        if self.spider_child == self.CHILD_GOODS_CATEGORIES:
            for category in self.category_goods_list:
                yield Request(
                    "{}{}".format(self.base_url, category['url']),
                    callback=GoodsList.parse,
                    headers=dict(referer=self.base_url),
                    meta=dict(only_category=True, spider=self)
                )

        # 评论采集方式: get_simple() 时间顺序 获取1次
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            db_session = Goods.get_db_session()
            self.goods_model_list = Goods.get_all_model(db_session, {'site_id': self.site_id})
            print('===============total : = ' + str(len(self.goods_model_list)))
            for model in self.goods_model_list:
                yield self.get_request_goods_detail(model)

        if self.spider_child == CHILD_GOODS_LIST_RANKING:
            category_name = self.input_args["category_name"]  # 'Women Sports Tees & Tanks'
            goods_list_url = self.input_args['url']  # '/Women-Sports-Tees-Tanks-c-2185.html'

            ranking_log_id = 0
            if 'ranking_log_id' in self.input_args:
                ranking_log_id = int(self.input_args['ranking_log_id'])

            sort_by = 7
            if 'sort_by' in self.input_args:
                sort_by = int(self.input_args['sort_by'])

            rank_type = EnumGoodsRanking.TYPE_TOP_REVIEWS
            if 'rank_type' in self.input_args:
                rank_type = self.input_args['rank_type']

            # 最终数据管道保存goods_item信息到数据库时，先保存或更新goods, 再存储 goods和ranking_log 的对应关系
            self.ranking_log = self.get_ranking_log(category_name, rank_type, log_id=ranking_log_id)

            page = 1
            url = "{}{}?{}".format(self.base_url, goods_list_url, urlencode({'page': page, 'sort': sort_by}))
            meta = dict(spider=self, categories_map=self.categories_map)
            yield self.get_request_goods_list(url, meta)

        # 评论采集方式: get_all() 时间逆序 获取最近N个月评论
        if self.spider_child == CHILD_GOODS_REVIEWS_BY_RANKING:
            category_name = self.input_args["category_name"]  # 'Women Sports Tees & Tanks'
            ranking_log = self.get_ranking_log_real(category_name, EnumGoodsRanking.TYPE_TOP_REVIEWS)
            db_session = RankingGoods.get_db_session()
            ranking_goods_list = RankingGoods.get_all_model(db_session, {'ranking_log_id': ranking_log.id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model = Goods.get_model(db_session, {'id': xgd.goods_id})
                yield self.get_request_goods_detail(model)

    def get_categories_map(self):
        db_session = GoodsCategory.get_db_session()
        categories = GoodsCategory.get_all_model(db_session, {'site_id': self.site_id})
        categories_map = {}
        for cat_model in categories:
            categories_map[cat_model.code] = cat_model
        return categories_map

    def closed(self, reason):
        super(SheinSpider, self).closed(reason)
        print("============Close Spider : " + self.name)
        if self.spider_child == self.CHILD_GOODS_CATEGORIES:
            # 关联已保存的category的parent_id
            db_session = GoodsCategory.get_db_session()
            all_model = GoodsCategory.get_all_model(db_session, {'site_id': self.site_id})
            for model in all_model:
                p_model = GoodsCategory.get_model(db_session, {'code': model.parent_code, 'site_id': self.site_id})
                if p_model:
                    model.parent_id = p_model.id
            db_session.commit()


