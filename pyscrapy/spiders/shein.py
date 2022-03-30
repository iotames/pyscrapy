from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.shein_goods_list import GoodsList
from pyscrapy.grabs.shein_goods import GoodsDetail
from pyscrapy.extracts.shein import BASE_URL
from pyscrapy.models import GoodsCategory, Goods, RankingGoods, RankingLog
from pyscrapy.enum.shein import EnumGoodsRanking
from pyscrapy.enum.spider import *  # CHILD_GOODS_REVIEWS_BY_RANKING
import time


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
        'COMPONENTS_NAME_LIST_DENY': []
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
        },
        {
            "total_page": 40,
            "url": "/Sports-c-3195.html",
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
        return

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
            ranking_log_id = self.input_args["ranking_log_id"] if "ranking_log_id" in self.input_args else 0
            if ranking_log_id > 0:
                goods_models = []
                rank_goods_list = RankingGoods.get_all_model(db_session, {"ranking_log_id": ranking_log_id})
                for rank_goods in rank_goods_list:
                    goods_model = Goods.get_model(db_session, {"id": rank_goods.goods_id})
                    goods_models.append(goods_model)
                self.goods_model_list = goods_models
            else:
                self.goods_model_list = Goods.get_all_model(db_session, {'site_id': self.site_id})
            print('===============total : = ' + str(len(self.goods_model_list)))
            # skipI = 1
            for model in self.goods_model_list:
                # TODO detail_collected_at
                # if time.time() - model.updated_at < 3600*24:
                #     print(f"---Skip:{str(skipI)}--Url:{model.url}--")
                #     skipI += 1
                #     continue
                yield Request(model.url, callback=GoodsDetail.parse, headers=dict(referer=self.base_url),
                              meta=dict(spider=self, categories_map=self.categories_map, goods_model=model))

        if self.spider_child == CHILD_GOODS_REVIEWS:
            url = self.input_args.get('url')  # https://shefit.com/products/leggings-boss
            goods_model = Goods.get_model(self.db_session, {'url': url})
            yield Request(url, callback=GoodsDetail.parse, headers=dict(referer=self.base_url),
                          meta=dict(spider=self, categories_map=self.categories_map, goods_model=goods_model))

        if self.spider_child == CHILD_GOODS_LIST_RANKING:
            category_name = self.input_args["category_name"] if 'category_name' in self.input_args else "" # 'Women Sports Tees & Tanks'
            goods_list_url = self.input_args['url'] if 'url' in self.input_args else "" # '/Women-Sports-Tees-Tanks-c-2185.html'

            ranking_log_id = int(self.input_args['ranking_log_id']) if 'ranking_log_id' in self.input_args else 0

            sort_by = 7
            page = 1
            if 'sort_by' in self.input_args:
                sort_by = int(self.input_args['sort_by'])

            rank_type = EnumGoodsRanking.TYPE_TOP_REVIEWS
            if 'rank_type' in self.input_args:
                rank_type = self.input_args['rank_type']

            # 最终数据管道保存goods_item信息到数据库时，先保存或更新goods, 再存储 goods和ranking_log 的对应关系
            if ranking_log_id:
                self.ranking_log_id = ranking_log_id
                ranking_log = RankingLog.get_log(self.db_session, self.site_id, "", rank_type, ranking_log_id)
                goods_list_url = ranking_log.url
            else:
                self.create_ranking_log(category_name, rank_type)
                url = f"{self.get_site_url(goods_list_url)}?{urlencode({'page': page, 'sort': sort_by})}"
                RankingLog.save_update({"id": self.ranking_log_id}, {"url": url})
            
            url = f"{self.get_site_url(goods_list_url)}?{urlencode({'page': page, 'sort': sort_by})}"
            meta = dict(spider=self, categories_map=self.categories_map)

            yield self.get_request_goods_list(url, meta)

        # 评论采集方式: get_all() 时间逆序 获取最近N个月评论
        if self.spider_child == CHILD_GOODS_REVIEWS_BY_RANKING:
            if 'ranking_log_id' not in self.input_args:
                raise RuntimeError("缺少ranking_log_id参数")
            self.ranking_log_id = int(self.input_args['ranking_log_id'])
            ranking_goods_list = RankingGoods.get_all_model(self.db_session, {'ranking_log_id': self.ranking_log_id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model = Goods.get_model(self.db_session, {'id': xgd.goods_id})
                yield Request(model.url, callback=GoodsDetail.parse, headers=dict(referer=self.base_url),
                              meta=dict(spider=self, categories_map=self.categories_map, goods_model=model))

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


