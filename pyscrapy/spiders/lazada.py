from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from pyscrapy.enum.spider import *
from urllib.parse import urlencode


class LazadaSpider(BaseSpider):

    name = NAME_LAZADA

    base_url = "https://www.lazada.com.ph"

    api_url = "https://www.lazada.com.ph/catalog/"

    total_page = 0

    def get_goods_list_request(self, page: int, keyword: str):
        params = {
            "_keyori": "ss",
            "ajax": "true",
            "from": "input",
            "spm": "a2o4l.home.search.go.4a14359dKIEDlX",
            "page": page,
            "q": keyword,
        }
        url = self.api_url + "?" + urlencode(params)
        return Request(url, self.parse_goods_list, meta=dict(keyword=keyword))

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        # 'COOKIES_ENABLED': True,
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    def __init__(self, name=None, **kwargs):
        super(LazadaSpider, self).__init__(name=name, **kwargs)

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            self.total_page = 20
            keyword = "maternity"
            yield self.get_goods_list_request(1, keyword)
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
                    yield Request(self.get_site_url(model.url), headers={'referer': self.base_url + "/en"},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        keyword = meta['keyword']
        json_res = response.json()
        main_info = json_res['mainInfo']
        page = int(main_info['page'])
        limit = int(main_info['pageSize'])
        total = int(main_info['totalResults'])

        list_items = json_res['mods']['listItems']
        count_goods = 0
        for item in list_items:
            status = Goods.STATUS_AVAILABLE if item['isStock'] else Goods.STATUS_SOLD_OUT
            code = item['itemId']
            title = item['name']
            price = item['price']
            price_text = item['priceShow']
            url = item['productUrl']
            image = item['image']
            reviews_num = item['review']
            spu = item['sellerId']
            details = {
                'brand': item['brandName'],
                'original_price': item['originalPrice'],
                'discount': item['discount'],
                'location': item['location'],
                'rating_score': item['ratingScore']
            }
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['url'] = url
            goods_item['code'] = code
            goods_item['price'] = price
            goods_item['price_text'] = price_text
            goods_item['title'] = title
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['reviews_num'] = reviews_num
            goods_item['asin'] = spu
            goods_item['status'] = status
            goods_item['details'] = details
            yield goods_item
            count_goods += 1

        if self.total_page > 0 and page < self.total_page:
            yield self.get_goods_list_request(page+1, keyword)

        if self.total_page == 0 and (page * limit < total):
            yield self.get_goods_list_request(page + 1, keyword)

    def parse_goods_detail(self, response: TextResponse):
        pass



