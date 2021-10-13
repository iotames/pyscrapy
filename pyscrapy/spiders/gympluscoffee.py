import scrapy
from scrapy.http import TextResponse, request
from ..items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem
from ..helpers import Logger
from ..models import Goods, GoodsSku
from Config import Config
from ..database import Database
import json
from sqlalchemy import and_, or_
import time


class GympluscoffeeSpider(scrapy.Spider):
    name = 'gympluscoffee'
    site_id = 1
    domain = 'gympluscoffee.com'
    base_url = 'https://gympluscoffee.com'
    allowed_domains = ['gympluscoffee.com']
    start_categories = ['merch', 'mens', 'womens']
    start_urls = []
    categories_info = {}
    url_to_category_name_map = {}
    goods_url_to_model_map = {}
    db_session = None
    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    spider_child = CHILD_GOODS_LIST

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)

        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

        if 'spider_child' in kwargs:
            if kwargs['spider_child'] == self.CHILD_GOODS_DETAIL:
                self.spider_child = self.CHILD_GOODS_DETAIL
                # 12小时内的商品不会再更新
                before_time = time.time() - (12 * 3600)
                goods_list = self.db_session.query(Goods).filter(or_(and_(
                    Goods.site_id == self.site_id,
                    Goods.updated_at < before_time
                ), Goods.status == Goods.STATUS_UNKNOWN)).all()
                for goods in goods_list:
                    self.start_urls.append(goods.url)
                    self.goods_url_to_model_map[goods.url] = goods
                    # spider.request_goods_detail(gd.url, gd)
        else:
            for category in self.start_categories:
                self.start_urls.append("{}/collections/{}?page=1".format(self.base_url, category))
                self.categories_info[category] = {'id': 0}
                self.url_to_category_name_map["{}/collections/{}".format(self.base_url, category)] = category
        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)

    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield request.Request(url, dont_filter=True)

    def parse(self, response: TextResponse, **kwargs):
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            yield self.save_goods_detail(response, self.goods_url_to_model_map[response.url])
            # yield scrapy.Request(url=url, callback=self.save_goods_detail, cb_kwargs={'goods_model': goods})

        if self.spider_child == self.CHILD_GOODS_LIST:
            goods_list = response.xpath('//a[@class="product-info__caption "]')
            # page_ele = response.xpath('//div[@id="bc-sf-filter-bottom-pagination"]/span[@class="page"][last()]')
            if not goods_list:
                return False
            request_url = response.url
            # self.save_goods_list(goods_list, request_url)
            self.mylogger.debug("request_url: " + request_url)
            url_info = request_url.split('?')
            current_page = int(url_info[1].split('=')[1])
            category_name = ''
            if url_info[0] in self.url_to_category_name_map:
                category_name = self.url_to_category_name_map[url_info[0]]
                category_item = GympluscoffeeCategoryItem()
                category_item['name'] = category_name
                yield category_item

            items = GympluscoffeeGoodsItem()
            for goods in goods_list:
                # href = goods.xpath('@href').extract()[0]
                href = goods.xpath('@href').get()
                title = goods.xpath('.//div/span[1]/text()').get()
                items['goods_title'] = title
                items['goods_url'] = href
                items['category_name'] = category_name
                items['category_id'] = self.categories_info[category_name]['id']
                # self.mylogger.debug('GOODS: ' + title + " : " + href)
                yield items

            next_url = url_info[0] + "?page=" + str(current_page + 1)
            yield scrapy.Request(url=next_url, callback=self.parse)

    def save_goods_detail(self, response: TextResponse, goods_model: Goods):
        if response.status != 200:
            self.mylogger.debug("Warning: " + response.url + " : status = " + str(response.status))
            goods_model.status = Goods.STATUS_UNAVAILABLE
            goods_model.updated_at = int(time.time())
            self.db_session.commit()
            return False
        select = response.xpath('//div[@class="purchase-details"]/div/button/span/text()')
        btn_text = select.get().strip()
        if btn_text == 'Sold Out':
            goods_model.status = Goods.STATUS_SOLD_OUT
            self.mylogger.debug("Warning: STATUS_SOLD_OUT: " + response.url)
        if btn_text == 'Add to Cart':
            goods_model.status = Goods.STATUS_AVAILABLE
        cc = response.text.split('window.wn.product')
        dd = cc[1][70:]
        ff = dd[0:(len(dd) - 10)]
        skus = json.loads(ff.strip())
        for sku in skus:
            sku_code = sku['id']
            sku_model = self.db_session.query(GoodsSku).filter(
                GoodsSku.goods_id == goods_model.id, GoodsSku.code == sku_code).first()
            update_data = {
                'code': sku_code,
                'option1': sku['option1'],
                'option2': sku['option2'],
                'option3': sku['option3'],
                'title': sku['sku'],
                'full_title': sku['name'],
                'price': sku['price'],
                'inventory_quantity': sku['inventory_quantity'],
                'barcode': sku['barcode']
            }

            if 'featured_image' in sku:
                if sku['featured_image']:
                    if 'src' in sku['featured_image']:
                        update_data['image'] = sku['featured_image']['src']
                    if 'product_id' in sku['featured_image']:
                        goods_model.code = sku['featured_image']['product_id']

            if not sku_model:
                sku_model = GoodsSku(**update_data)
                self.db_session.add(sku_model)
            else:
                update_data['updated_at'] = int(time.time())
                self.db_session.query(GoodsSku).filter(
                    GoodsSku.goods_id == goods_model.id, GoodsSku.code == sku_code).update(update_data)

        goods_model.updated_at = int(time.time())
        self.db_session.commit()
        print('SUCCESS update : ' + str(goods_model.id) + " title : " + goods_model.title)
