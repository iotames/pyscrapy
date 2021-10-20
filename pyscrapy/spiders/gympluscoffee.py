import scrapy
from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from ..items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, GympluscoffeeGoodsSkuItem
from ..models import Goods, GoodsSku, GoodsCategory
import json
from sqlalchemy import and_, or_
import time
from .basespider import BaseSpider
from translate import Translator


class GympluscoffeeSpider(BaseSpider):

    name = 'gympluscoffee'
    start_categories = ['merch', 'mens', 'womens']
    # categories_info = {}
    url_to_category_name_map = {}
    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    CHILD_GOODS_CATEGORIES = 'goods_categories'
    spider_child = CHILD_GOODS_CATEGORIES

    xpath_categories = '//ul[@class="list-menu list-menu--inline"]/li/div[@class="header-menu-item-father"]'
    xpath_product_desc = '//div[@class="product__description rte"]'
    xpath_product_reviews = '//span[@class="jdgm-prev-badge__text"]'

    translator: Translator

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)

        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        self.translator = Translator(to_lang='chinese')

    def to_chinese(self, content: str):
        return self.translator.translate(content)

    def start_requests(self):
        self.add_spider_log()
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # goods = self.db_session.query(Goods).filter(Goods.id == 543).first()
            # yield Request(goods.url, callback=self.parse, meta={'goods': goods})
            # 12小时内的商品不会再更新
            before_time = time.time() - (12 * 3600)
            goods_list = self.db_session.query(Goods).filter(or_(and_(
                Goods.site_id == self.site_id,
                Goods.updated_at < before_time
            ), Goods.status == Goods.STATUS_UNKNOWN)).all()
            for goods in goods_list:
                print("goods id = " + str(goods.id) + "==== status = " + str(goods.status) + " url = " + goods.url)
                yield Request(goods.url, callback=self.parse, meta={'goods': goods})

        if self.spider_child == self.CHILD_GOODS_LIST:
            categories = self.db_session.query(GoodsCategory).filter(and_(
                GoodsCategory.site_id == self.site_id, GoodsCategory.parent_id > 0)).all()
            for category in categories:
                start_url = category.url + "?page=1"
                self.start_urls.append(start_url)
                print(start_url)
                yield Request(start_url, callback=self.parse, meta={'category': category, 'page': 1})

        if self.spider_child == self.CHILD_GOODS_CATEGORIES:
            yield Request(self.base_url, callback=self.parse)

    def get_categories(self, response: TextResponse) -> list:
        categories_ele = response.xpath(self.xpath_categories)
        categories = []
        for category_ele in categories_ele:
            name = category_ele.xpath('summary/span/text()').get().strip()
            category = {'name': name}
            items_ele = category_ele.xpath('ul/li/a')
            items = []
            i = 0
            for item_ele in items_ele:
                if i == 0:
                    url = item_ele.xpath('@href').get()
                    category['url'] = url
                    i += 1
                    continue
                name = item_ele.xpath('text()').get().strip()
                url = item_ele.xpath('@href').get()
                item = {'name': name, 'url': url}
                items.append(item)
            category['items'] = items
            categories.append(category)
        return categories

    def parse(self, response: TextResponse, **kwargs):
        if self.spider_child == self.CHILD_GOODS_CATEGORIES:
            categories = self.get_categories(response)
            for category in categories:
                p_model = self.db_session.query(GoodsCategory).filter(
                    GoodsCategory.site_id == self.site_id,
                    GoodsCategory.name == category['name'],
                    GoodsCategory.url == self.base_url + category['url']
                ).first()
                item_category = GympluscoffeeCategoryItem()
                item_category['site_id'] = self.site_id
                item_category['parent_name'] = None
                item_category['parent_url'] = None
                item_category['model'] = p_model
                item_category['name'] = category['name']
                item_category['url'] = category['url']
                yield item_category
                for item in category['items']:
                    model = self.db_session.query(GoodsCategory).filter(
                        GoodsCategory.site_id == self.site_id,
                        GoodsCategory.name == item['name'],
                        GoodsCategory.url == self.base_url + item['url']
                    ).first()
                    item_category = GympluscoffeeCategoryItem()
                    item_category['site_id'] = self.site_id
                    item_category['parent_name'] = category['name']
                    item_category['parent_url'] = category['url']
                    item_category['model'] = model
                    item_category['name'] = item['name']
                    item_category['url'] = item['url']
                    yield item_category
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            goods_model = response.meta['goods']
            item_goods = GympluscoffeeGoodsItem()
            item_goods['model'] = goods_model
            if response.status != 200:
                self.mylogger.debug("Warning: " + response.url + " : status = " + str(response.status))
                item_goods['status'] = Goods.STATUS_AVAILABLE
                item_goods['url'] = response.url
                yield item_goods

            desc_ele = response.xpath(self.xpath_product_desc)
            desc = desc_ele.xpath('span/p/text()').get().strip()  # 描述
            print(desc)
            reviews_text: str = response.xpath(self.xpath_product_reviews + '/text()').get().strip()
            reviews = int(reviews_text.replace(',', '').split(' ')[0])
            print(reviews)
            fabric_html = desc_ele.xpath('div[6]/div[2][contains(.,text())]').get()
            dd = fabric_html.split('<div class="product_collapsible_content">')
            fabric = dd[1].split('</div>')[0].replace('<br>', ' ').strip()  # 织物材料
            print(fabric)
            # print(self.to_chinese(fabric))
            # return False

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
                item_sku['inventory_quantity'] = sku['inventory_quantity']
                item_sku['barcode'] = sku['barcode']

                if 'featured_image' in sku:
                    if sku['featured_image']:
                        if 'src' in sku['featured_image']:
                            item_sku['image'] = sku['featured_image']['src']
                        if 'product_id' in sku['featured_image']:
                            item_goods['code'] = sku['featured_image']['product_id']
                yield item_sku

            yield item_goods

        if self.spider_child == self.CHILD_GOODS_LIST:
            goods_list = response.xpath('//a[@class="full-unstyled-link"]')
            # page_ele = response.xpath('//div[@id="bc-sf-filter-bottom-pagination"]/span[@class="page"][last()]')
            if goods_list:
                category: GoodsCategory = response.meta['category']
                request_url = response.url
                self.mylogger.debug("request_url: " + request_url)
                url_info = request_url.split('?')
                current_page = int(url_info[1].split('=')[1])
                items = GympluscoffeeGoodsItem()
                for goods in goods_list:
                    href: str = goods.xpath('@href').get()
                    goods_model = self.db_session.query(Goods).filter(Goods.url == self.base_url + href.strip()).first()
                    items['model'] = goods_model  # None: ADD ; Other: UPDATE
                    title: str = goods.xpath('.//div/span[1]/text()').get()
                    items['title'] = title.strip()
                    items['url'] = href.strip()
                    items['category_name'] = category.name
                    items['category_id'] = category.id
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
