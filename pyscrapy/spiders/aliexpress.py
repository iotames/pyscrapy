import re
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from urllib.parse import urlencode
from pyscrapy.enum.spider import *


class AliexpressSpider(BaseSpider):

    name = NAME_ALIEXPRESS

    base_url = "https://es.aliexpress.com"

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

    max_page = 5

    def __init__(self, name=None, **kwargs):
        super(AliexpressSpider, self).__init__(name=name, **kwargs)
        self.domain = "es.aliexpress.com"
        self.base_url = "https://" + self.domain
        self.image_referer = self.base_url + "/"

    categories_list = [
        {'code': '204000363', 'name': 'bicycle-accessories'}
    ]

    def request_goods_list(self, page: int, category_name: str, category_code: str):
        pre_url = self.get_site_url(f"/category/{category_code}/{category_name}.html")
        # trafficChannel=main&catName=bicycle-accessories&CatId=204000363&ltype=wholesale&SortType=default&page=2
        if page < 1:
            raise ValueError("page must begin 1")
        url = pre_url
        referer = self.image_referer
        query = {
            "trafficChannel": "main",
            "catName": category_name,
            "CatId": category_code,
            "ltype": "wholesale",
            "SortType": "default",
            "page": page
        }
        if page == 1:
            url = pre_url
        if page == 2:
            url = f"{pre_url}?{urlencode(query)}"
        if page > 2:
            query["isrefine"] = "y"
            url = f"{pre_url}?{urlencode(query)}"
        return Request(url, self.parse_goods_list, 'GET', headers=dict(referer=referer),
                       meta=dict(page=page, category_code=category_code, category_name=category_name))

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            # https://es.aliexpress.com/category/204000363/bicycle-accessories.html
            # https://es.aliexpress.com/category/204000363/bicycle-accessories.html?trafficChannel=main&catName=bicycle-accessories&CatId=204000363&ltype=wholesale&SortType=default&page=2
            # https://es.aliexpress.com/category/204000363/bicycle-accessories.html?trafficChannel=main&catName=bicycle-accessories&CatId=204000363&ltype=wholesale&SortType=default&page=3&isrefine=y
            # https://es.aliexpress.com/category/204000363/bicycle-accessories.html?trafficChannel=main&catName=bicycle-accessories&CatId=204000363&ltype=wholesale&SortType=default&page=4&isrefine=y
            # https://es.aliexpress.com/glosearch/api/product?trafficChannel=main&catName=bicycle-accessories&CatId=204000363&ltype=wholesale&SortType=default&page=9&isrefine=y&origin=y&pv_feature=4000542756074,32890799830,1005003311012459,1005002097247672,1005003251488155,1005003499233669,1005003474856095,1005002951860723,32857236296,4001340136889,1005003542475964,32917149930,1005002978690772,1005003062315423,1005003474883690,1005002695293393,1005003058534154,1005001426275071,32811852634,1005003412592303,1005002862994511,1005001929193854,1005001809930119,1005001657455850,1005002782819828,1005002064571588,4000015238385,4001050781118,1005002388294611,1005003634848099,1005001685745068,1005002919816556,1005001672441280,1005003510207881,1005001840482171,4000619115978,4000538040172,33032342450,1005002063777106,1005002134287049
            yield self.request_goods_list(1, 'bicycle-accessories', '204000363')
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time()
            if self.app_env == self.spider_config.ENV_PRODUCTION:
                before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id, or_(
                    Goods.status == Goods.STATUS_UNKNOWN,
                    Goods.updated_at < before_time)
            )).all()
            goods_list_len = len(self.goods_model_list)
            print('=======goods_list_len============ : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield Request(self.get_site_url(model.url), headers={'referer': self.base_url},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    re_run_params = "window.runParams = (.+?);"

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        re_run_params = self.re_run_params
        run_params_list = re.findall(re_run_params, response.text)
        run_params = json.loads(run_params_list[1])
        goods_items = run_params["mods"]["itemList"]["content"]
        for goods in goods_items:
            print(goods)
            image = goods["image"]["imgUrl"]
            code = goods["productId"]
            # store_url = goods['store']['storeUrl']  # storeName, storeId
            title = goods['title']['displayTitle']
            reviews_num = goods['evaluation']['starWidth']  # starRating starHeight
            price_info = goods['prices']
            price = price_info["salePrice"]['minPrice']
            price_text = price_info["salePrice"]['formattedPrice']

            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            # goods_item['title'] = goods['name']
            # goods_item['url'] = goods['url']
            yield goods_item

        if meta['page'] < self.max_page:
            next_page = meta['page'] + 1
            yield self.request_goods_list(next_page, meta['category_name'], meta['category_code'])



