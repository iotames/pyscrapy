import re

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


class RidestoreSpider(BaseSpider):

    name = 'ridestore'

    base_url = "https://www.ridestore.com"

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
        {'category_name': 'montec', 'url': '/montec', 'total_page': 16},
        {'category_name': 'dope', 'url': '/dope', 'total_page': 25}
    ]

    xpath_goods_items = '//article[@class="UdJV cO0x"]/a'
    xpath_goods_title = '@aria-label'  # div[2]/div/div[1]/text()
    xpath_goods_url = '@href'
    xpath_goods_image = 'div/div/img/@src'
    xpath_goods_price = 'div[2]/div/div[2]/span/text()'  # 209,90 €\xa0   strip()

    xpath_detail_color = '//div[@class="dqKi"]/text()'

    xpath_json_product = '//script[@id="json-product"]/text()'

    def __init__(self, name=None, **kwargs):
        super(RidestoreSpider, self).__init__(name=name, **kwargs)

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for category in self.goods_list_urls:
                url = self.get_site_url(category['url'])
                yield Request(
                    url,
                    callback=self.parse_goods_list,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1, category_name=category['category_name'], total_page=category['total_page'])
                )
        # TODO 点一次未更新完整，要多点几次。 原因为 URL 重复?
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
        total_page = meta['total_page']
        category_name = meta['category_name']

        eles = response.xpath(self.xpath_goods_items)
        goods_list_len = len(eles)  # 28
        print('=====page====goods_list_len===={}==={}=='.format(str(page), str(str(goods_list_len))))
        self.goods_list_count += goods_list_len
        print('=========total goods =======' + str(goods_list_len))

        for ele in eles:
            goods_ele = BaseElement(ele)
            title = goods_ele.get_text(self.xpath_goods_title)
            price_text = goods_ele.get_text(self.xpath_goods_price)
            price = 0
            if price_text:
                price = int(price_text.split(' ')[0])
            url = goods_ele.get_text(self.xpath_goods_url)
            if not url:
                return False
            url = self.get_site_url(url)
            # code = url.split('-')[-1]
            image = goods_ele.get_text(self.xpath_goods_image)
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['category_name'] = category_name
            # goods_item['code'] = code
            goods_item['title'] = title
            if image:
                goods_item['image'] = image
                goods_item['image_urls'] = [image]
            goods_item['url'] = url
            goods_item['price_text'] = price_text
            goods_item['price'] = price
            yield goods_item

        if page < total_page:
            next_url = "{}/{}?page={}".format(self.base_url, category_name, str(page + 1))
            yield Request(next_url, callback=self.parse_goods_list, meta=dict(page=page+1, category_name=category_name, total_page=total_page))

    statuses = {
        'InStock': Goods.STATUS_AVAILABLE,
        'SoldOut': Goods.STATUS_SOLD_OUT,
        'OutOfStock': Goods.STATUS_SOLD_OUT,
        'Discontinued': Goods.STATUS_UNAVAILABLE
    }

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        # availableQuantity 库存
        print('====parse_goods_detail====goods_id={}===='.format(str(model.id)))

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


