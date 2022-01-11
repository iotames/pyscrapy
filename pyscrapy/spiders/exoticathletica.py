from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from pyscrapy.enum.spider import *


class ExoticathleticaSpider(BaseSpider):

    name = NAME_EXOTICATHLETICA

    base_url = "https://www.exoticathletica.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    categories = [
        'new', 'activewear', 'black-essentials', 'tops', 'bottoms', 'dresses', 'outerwear', 'swimwear', 'kids',
        # 'accessories', 'all', 'clearance'
    ]

    goods_code_list = []

    def __init__(self, name=None, **kwargs):
        super(ExoticathleticaSpider, self).__init__(name=name, **kwargs)

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for category in self.categories:
                yield Request(
                    self.get_site_url(f"/collections/{category}"),
                    callback=self.parse_goods_list,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1, category=category)
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
                    # url = model.url + ".json"
                    handle = model.url.split('/')[-1]
                    url = self.get_site_url(f"/products/{handle}.js")
                    yield Request(url, headers={'referer': self.base_url},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        category = meta['category']
        total_ele = response.xpath('//p[@class="medium-up--hide text-center"]/text()')
        total_text = total_ele.get()
        total_num = int(total_text.split(' ')[0])
        limit = 80
        products_eles = response.xpath('//div[@class="grid-product__content"]')
        for product_ele in products_eles:
            url_ele = product_ele.xpath('a/@href')  # [@class="grid-product__link"]
            url_text = url_ele.get() if url_ele else ""
            if not url_text:
                continue
            code = product_ele.xpath('parent::div/@data-product-id').get()
            if code in self.goods_code_list:
                # 剔除不同分类中的重复商品
                continue
            self.goods_code_list.append(code)
            url = self.get_site_url(url_text)
            title_ele = product_ele.xpath('a//div[@class="grid-product__title grid-product__title--body"]/text()')
            title = title_ele.get().strip() if title_ele else ""
            price_ele = product_ele.xpath('a//span[@class="money"]/text()')
            price_text = price_ele.get() if price_ele else ""
            img_ele = product_ele.xpath('a//div[@class="image-wrap"]/img/@data-src')
            img_text = img_ele.get() if img_ele else ""
            image = "https:" + img_text.replace("{width}", "360") if img_text else ""

            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['code'] = code
            goods_item['category_name'] = category
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['price_text'] = price_text
            if image:
                goods_item['image'] = image
                goods_item['image_urls'] = [image]
            yield goods_item
        if limit * page < total_num:
            yield Request(
                self.get_site_url(f"/collections/{category}?page={str(page+1)}"),
                callback=self.parse_goods_list,
                meta=dict(page=page+1, category=category)
            )

    def parse_goods_detail(self, response: TextResponse):
        # USE https://www.exoticathletica.com/collections/fashion-tops/products/black-rib-knit-twist-front-cropped-tank.json
        # https://www.exoticathletica.com/products/black-rib-knit-twist-front-cropped-tank.js
        meta = response.meta
        model: Goods = meta['model']
        json_data = response.json()
        # product = json_data['product']
        product = json_data
        code = str(product['id'])
        if code != model.code:
            raise ValueError("goods code error")
        title = product['title']
        variants = product['variants']
        quantity = 0
        sku_list = []
        price = product['price'] / 100
        status = Goods.STATUS_AVAILABLE if product['available'] else 0
        for sku_info in variants:
            # price = sku_info['price']
            sku_inventory = sku_info['inventory_quantity']
            sku_detail = {
                'title': sku_info['title'],
                'sku': sku_info['sku'],
                'quantity': sku_inventory
            }
            sku_list.append(sku_detail)
            quantity += sku_inventory

        details = {'sku_list': sku_list}
        goods_item = BaseGoodsItem()
        goods_item['model'] = model
        goods_item['spider_name'] = self.name
        goods_item['code'] = code
        goods_item['status'] = status
        goods_item['price'] = price
        goods_item['title'] = title
        goods_item['details'] = details
        goods_item['quantity'] = quantity
        yield goods_item


