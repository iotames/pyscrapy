import re
from urllib.parse import urlencode
import json
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config

from pyscrapy.enum.spider import NAME_LULULEMON


class LululemonSpider(BaseSpider):
    """
    us.shein.com 露露柠檬电商平台
    """

    name = NAME_LULULEMON

    base_url = "https://shop.lululemon.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    goods_list_urls = [
        '/api/c/women'
        '/api/c/men',
    ]

    def __init__(self, name=None, **kwargs):
        super(LululemonSpider, self).__init__(name=name, **kwargs)
        self.domain = "shop.lululemon.com"
        self.base_url = "https://www." + self.domain
        self.allowed_domains = [self.domain]

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for url in self.goods_list_urls:
                yield Request(
                    "{}?{}".format(self.get_site_url(url), urlencode(dict(page=1, page_size=9))),
                    callback=self.parse_goods_list,
                    headers=dict(referer=self.get_site_url(url)),
                    meta=dict(page=1, page_size=9, url=url)
                )

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

    goods_list_count = 0

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        page_size = meta['page_size']  # 9 or 45
        meta_url = meta['url']  # '/api/c/women' or '/api/c/men'

        next_page = page + 1
        next_page_size = page_size
        next_url = ""
        if page_size == 9 and page == 5:
            next_page = 2
            next_page_size = 45
            next_url = self.get_site_url(meta_url) + "?" + urlencode(dict(page=2, page_size=45))

        json_response = json.loads(response.text)

        links = json_response['links']  # first last next prev self
        self_page = int(links['self'].split('=')[1])  # self: "/c/men?page=3"
        last_page = int(links['last'].split('=')[1])  # self: "/c/men?page=11"
        if self_page < last_page:
            next_page = int(links['next'].split('=')[1])
            next_url = self.get_site_url(meta_url + "?" + urlencode(dict(page=next_page, page_size=next_page_size)))

        print('===========next url===={}===page={}==page_size={}=='.format(next_url, str(page), str(page_size)))

        data = json_response['data']
        attributes = data['attributes']
        main_content = attributes['main-content']
        goods_list = []
        for main in main_content:
            if main['type'] == "CDPResultsList":
                goods_list = main["records"]
        for info in goods_list:
            price = info['list-price'][0]
            currency = info['currency-code']
            color_list = info['color-group']
            details = {
                'color_num': len(color_list),
                'color_list': color_list
            }
            image = info['sku-sku-images'][0] + "?wid=320"
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['code'] = info['unified-id']
            goods_item['asin'] = info['repository-id']  # prod10020121
            goods_item['title'] = info['display-name']
            goods_item['price'] = price
            goods_item['price_text'] = price + currency
            goods_item['url'] = self.get_site_url(info['pdp-url'])
            goods_item['category_name'] = info['parent-category-unified-id']
            goods_item['details'] = details
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            yield goods_item
        if next_url:
            yield Request(
                next_url, callback=self.parse_goods_list,
                headers=dict(referer=self.get_site_url(meta_url)),
                meta=dict(page=next_page, page_size=next_page_size, url=meta_url)
            )

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        # availableQuantity 库存
        print('====parse_goods_detail====goods_id={}===='.format(str(model.id)))
"""
        re_detail = r"_EN={\"id\"(.+?);window.PRELOADED_DELIVERY_DATA"
        re_info = re.findall(re_detail, response.text)
        text = re_info[0]
        json_info_text = "{\"id\"" + text
        info = json.loads(json_info_text)
        brand = info['brand']
        color = info['color']
        desc = info['desc']
        category_name = info['productTypeCategory']['name']
        reviews_info = info['reviews']
        reviews_num = reviews_info['total_reviews']
        rating_value = reviews_info['average_score']

        json_product_text = response.xpath(self.xpath_json_product).get()
        # color = response.xpath(self.xpath_detail_color).get().strip()
        p_info = json.loads(json_product_text)
        offers = p_info['offers']
        price = offers['price']
        status_text = offers['availability'].split('/')[-1]
        condition_text = offers['itemCondition'].split('/')[-1]
        if condition_text != 'NewCondition':
            self.mylogger.debug("goods_id={}======{}".format(str(model.id), condition_text))
        if status_text != 'InStock':
            self.mylogger.debug("goods_id={}======{}".format(str(model.id), status_text))

        status = self.statuses[status_text] if status_text in self.statuses else Goods.STATUS_UNKNOWN

        image = p_info['image']

        details = {
            'brand': brand,
            'currency': offers['priceCurrency'],
            'rating_value': rating_value,
            'color': color,
            'desc': desc
        }
        goods_item = BaseGoodsItem()
        goods_item['model'] = model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        goods_item['image'] = image
        goods_item['code'] = p_info['sku']
        goods_item['title'] = p_info['name']
        goods_item['image_urls'] = [image + "?fit=max&w=450&q=70&dpr=2&usm=15&auto=format"]
        goods_item['url'] = response.url
        goods_item['price'] = price
        goods_item['reviews_num'] = reviews_num
        goods_item['status'] = status
        goods_item['details'] = details
        yield goods_item
"""

