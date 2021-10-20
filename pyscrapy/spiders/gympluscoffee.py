import scrapy
from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from ..items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, GympluscoffeeGoodsSkuItem
from ..models import Goods, GoodsSku
import json
from sqlalchemy import and_, or_
import time
from .basespider import BaseSpider


class GympluscoffeeSpider(BaseSpider):

    name = 'gympluscoffee'
    start_categories = ['merch', 'mens', 'womens']
    categories_info = {}
    url_to_category_name_map = {}
    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    spider_child = CHILD_GOODS_LIST

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)

        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)

        if kwargs['spider_child'] == self.CHILD_GOODS_DETAIL:
            self.spider_child = self.CHILD_GOODS_DETAIL

        if kwargs['spider_child'] == self.CHILD_GOODS_LIST:
            for category in self.start_categories:
                start_url = "{}/collections/{}?page=1".format(self.base_url, category)
                self.start_urls.append(start_url)
                self.categories_info[category] = {
                    'id': 0,
                    'url': "{}/collections/{}".format(self.base_url, category),
                    'start_url': start_url,
                    'name': category
                }

    def start_requests(self):
        self.add_spider_log()
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 12小时内的商品不会再更新
            before_time = time.time() - (12 * 3600)
            goods_list = self.db_session.query(Goods).filter(or_(and_(
                Goods.site_id == self.site_id,
                Goods.updated_at < before_time
            ), Goods.status == Goods.STATUS_UNKNOWN)).all()
            for goods in goods_list:
                yield Request(goods.url, callback=self.parse, meta={'goods': goods})
        else:
            for category_name, info in self.categories_info.items():
                yield Request(info['start_url'], callback=self.parse, meta={'category': info, 'page': 1})
                # yield Request(info['start_url'], callback=self.parse, meta={'category_name': category_name})

    def parse(self, response: TextResponse, **kwargs):
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            goods_model = response.meta['goods']
            item_goods = GympluscoffeeGoodsItem()
            item_goods['model'] = goods_model
            if response.status != 200:
                self.mylogger.debug("Warning: " + response.url + " : status = " + str(response.status))
                item_goods['status'] = Goods.STATUS_AVAILABLE
                item_goods['url'] = response.url
                yield item_goods

            xpath = '//div[@class="product-form__buttons"]/button/text()'
            select = response.xpath(xpath)
            btn_text: str = select.get().strip()
            if btn_text.lower() == 'sold out':
                item_goods['status'] = Goods.STATUS_SOLD_OUT
                self.mylogger.debug("Warning: STATUS_SOLD_OUT: " + response.url)
            if btn_text.lower() == 'add to cart':
                item_goods['status'] = Goods.STATUS_AVAILABLE
            skus = self.get_variants_by_html(response.text)
            for sku in skus:
                item_sku = GympluscoffeeGoodsSkuItem()
                sku_code = sku['id']
                sku_model = self.db_session.query(GoodsSku).filter(
                    GoodsSku.goods_id == goods_model.id, GoodsSku.code == sku_code).first()

                item_sku['site_id'] = self.site_id
                item_sku['model'] = sku_model
                item_sku['code'] = sku_code
                item_sku['goods_id'] = goods_model.id
                item_sku['category_id'] = goods_model.category_id
                item_sku['category_name'] = goods_model.category_name
                item_sku['options'] = [sku['option1'], sku['option2'], sku['option3']]
                item_sku['title'] = sku['sku']
                item_sku['full_title'] = sku['name']
                item_sku['price'] = sku['price']
                item_sku['inventory_quantity'] = sku['price']
                item_sku['barcode'] = sku['price']

                if 'featured_image' in sku:
                    if sku['featured_image']:
                        if 'src' in sku['featured_image']:
                            item_sku['image'] = sku['featured_image']['src']
                        if 'product_id' in sku['featured_image']:
                            item_goods['code'] = sku['featured_image']['product_id']
                yield item_sku

            yield item_goods

        if self.spider_child == self.CHILD_GOODS_LIST:
            if response.meta['page'] == 2:
                time.sleep(2)
            goods_list = response.xpath('//a[@class="full-unstyled-link"]')
            # page_ele = response.xpath('//div[@id="bc-sf-filter-bottom-pagination"]/span[@class="page"][last()]')
            if goods_list:
                category = response.meta['category']
                if response.meta['page'] == 1:
                    category_item = GympluscoffeeCategoryItem()
                    category_item['name'] = category['name']
                    category_item['url'] = category['url']
                    yield category_item
                request_url = response.url
                self.mylogger.debug("request_url: " + request_url)
                url_info = request_url.split('?')
                current_page = int(url_info[1].split('=')[1])
                category_name = category['name']
                items = GympluscoffeeGoodsItem()
                for goods in goods_list:
                    # href = goods.xpath('@href').extract()[0]
                    href: str = goods.xpath('@href').get()
                    goods_model = self.db_session.query(Goods).filter(Goods.url == self.base_url + href.strip()).first()
                    items['goods_model'] = goods_model # None: ADD ; Other: UPDATE
                    title: str = goods.xpath('.//div/span[1]/text()').get()
                    items['title'] = title.strip()
                    items['url'] = href.strip()
                    items['category_name'] = category_name
                    items['category_id'] = self.categories_info[category_name]['id']
                    # self.mylogger.debug('GOODS: ' + title + " : " + href)
                    yield items
                next_url = url_info[0] + "?page=" + str(current_page + 1)
                yield Request(url=next_url, callback=self.parse, meta={'category': category, 'page': current_page + 1})

    @staticmethod
    def get_variants_by_html(html: str) -> list:
        cc = html.split("<script type=\"application/json\">")
        if len(cc) == 1:
            return []
        vv = cc[1].split('</script>')
        variants_str = vv[0].strip()
        return json.loads(variants_str)
