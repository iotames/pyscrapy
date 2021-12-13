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


class ShefitSpider(BaseSpider):

    name = 'shefit'

    base_url = "https://shefit.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    def __init__(self, name=None, **kwargs):
        super(ShefitSpider, self).__init__(name=name, **kwargs)
        self.base_url = "https://" + self.domain

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            url = self.get_site_url('/collections/shefit')
            yield Request(
                url,
                callback=self.parse_goods_list,
                headers=dict(referer=self.base_url)
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
        xpath = '//div[@class="twelve columns medium-down--one-whole"]/script/text()'
        json_text = response.xpath(xpath).get()

        json_info = json.loads(json_text)
        goods_items = json_info['itemListElement']
        goods_list_len = len(goods_items)  # 43
        print('=========total goods =======' + str(goods_list_len))
        for goods in goods_items:
            print(goods)
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['title'] = goods['name']
            goods_item['url'] = goods['url']
            yield goods_item

    statuses = {
        'InStock': Goods.STATUS_AVAILABLE,
        'SoldOut': Goods.STATUS_SOLD_OUT,
        'OutOfStock': Goods.STATUS_SOLD_OUT,
        'Discontinued': Goods.STATUS_UNAVAILABLE
    }

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        re_rule0 = r"\"Viewed Product\",(.+?)\);"
        re_info0 = re.findall(re_rule0, response.text)
        info0 = json.loads(re_info0[0])
        spu = info0['productId']
        price = info0['price']
        currency = info0['currency']
        price_text = price + currency
        category_name = info0['category']
        print('====parse_goods_detail====goods_id={}===='.format(str(model.id)))
        re_rule = r"productVariants=(.+?);"
        re_info = re.findall(re_rule, response.text)
        text = re_info[0]
        product_variants = json.loads(text)
        print(product_variants)
        quantity = 0
        sku_list = []
        for product in product_variants:
            sku_inventory = product['inventory_quantity']
            sku_info = {'title': product['title'], 'sku': product['sku'], 'name': product['name'], 'quantity': sku_inventory}
            sku_list.append(sku_info)
            quantity += sku_inventory

        details = {
            'sku_list': sku_list
        }

        xpath_json = '//script[@type="application/ld+json"]/text()'
        json_product_text = response.xpath(xpath_json)[1].get()
        print('======json_product_text===========')
        print(json_product_text)
        p_info = json.loads(json_product_text, strict=False)
        print(p_info)
        title = p_info['name']
        url = p_info['url']
        # sku_code = p_info['sku']  # 140003-011
        desc = p_info['description']
        image_text: str = p_info['image'][0]
        image_text = image_text.split('?')[0]
        last_str = image_text.split('_')[-1]
        img_ext = last_str.split('.')[-1]  # jpg gif
        image = image_text.replace(last_str, '200x.' + img_ext)
        status = Goods.STATUS_UNAVAILABLE
        offers = p_info['offers']

        for sku in offers:
            """
            {
                "@type" : "Offer","sku": "140003-011","availability" : "http://schema.org/InStock",
                "price" : "68.0", "priceCurrency" : "USD",
                "url" : "https://shefit.com/products/boss-leggings-conquer?variant=38474305700009"
            }
            """
            # price = sku['price']
            # price_text = price + sku['priceCurrency']
            status_text = sku['availability'].split('/')[-1]
            if status_text == 'InStock':
                status = self.statuses[status_text]

        goods_item = BaseGoodsItem()
        goods_item['model'] = model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        goods_item['image'] = image
        goods_item['code'] = spu
        goods_item['title'] = title
        goods_item['image_urls'] = [image]
        goods_item['url'] = response.url
        goods_item['price'] = price
        goods_item['price_text'] = price_text
        # goods_item['reviews_num'] = reviews_num
        goods_item['status'] = status
        goods_item['details'] = details
        goods_item['quantity'] = quantity
        yield goods_item


