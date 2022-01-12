# from scrapy.utils.project import get_project_settings 全局设置
from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from ..items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, GympluscoffeeGoodsSkuItem
from ..models import Goods, GoodsSku, GoodsCategory
import json
from sqlalchemy import and_, or_
import time
from .basespider import BaseSpider
from pyscrapy.enum.spider import *
# from translate import Translator
from Config import Config


class GympluscoffeeSpider(BaseSpider):

    name = NAME_GYMPLUSCOFFEE

    # TODO POST https://api-v3.findify.io/v3/smart-collection/collections/all
    # {"user":{"uid":"43vleHy1gvMLx39i","sid":"fCFPjZZsb7SHWOoH","persist":true,"exist":true},"t_client":1641979818801,"key":"ac020bc1-a0e6-4c90-9fe5-5f4d187825aa","filters":[],"limit":24,"offset":0,"slot":"collections/all"}

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    goods_model_list: list
    start_categories = ['merch', 'mens', 'womens']
    spider_child = CHILD_GOODS_CATEGORIES

    xpath_categories = '//ul[@class="list-menu list-menu--inline"]/li/div[@class="header-menu-item-father"]'
    xpath_product_desc = '//div[@class="product__description rte"]'
    xpath_product_reviews = '//span[@class="jdgm-prev-badge__text"]'
    xpath_product_rating = '//div[@class="jdgm-histogram jdgm-temp-hidden"]/div[@class="jdgm-histogram__row"]'
    xpath_product_title = '//h1[@class="product__title"]'

    # translator: Translator

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)
        self.base_url = "https://" + self.domain
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        # self.translator = Translator(to_lang='chinese')

    # def to_chinese(self, content: str):
    #     return self.translator.translate(content)

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_DETAIL:
            # goods = self.db_session.query(Goods).filter(Goods.id == 1).first()
            # yield Request(goods.url, callback=self.parse, meta={'goods': goods})

            # 3小时内的采集过的商品不会再更新
            before_time = time.time() - (3 * 3600)
            goods_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id,
                or_(Goods.updated_at < before_time, Goods.status == Goods.STATUS_UNKNOWN)
            )).all()
            goods_list_len = len(goods_list)
            print(goods_list_len)
            # max_connect = get_project_settings().get('CONCURRENT_REQUESTS')  # 全局设置
            # 爬虫请求的最大并行数
            max_connect = self.settings.getint('CONCURRENT_REQUESTS')  # 局部设置
            int_len = goods_list_len // max_connect  # 取整
            last_len = goods_list_len % max_connect  # 取余
            print(int_len)
            print(last_len)
            self.goods_model_list = goods_list
            # TODO 异步并发请求待优化
            yield Request(self.base_url, callback=self.update_goods_detail)

        if self.spider_child == CHILD_GOODS_LIST:
            categories = self.db_session.query(GoodsCategory).filter(and_(
                GoodsCategory.site_id == self.site_id, GoodsCategory.parent_id > 0)).all()
            for category in categories:
                start_url = category.url + "?page=1"
                self.start_urls.append(start_url)
                print(start_url)
                yield Request(start_url, callback=self.parse, meta={'category': category, 'page': 1})

        if self.spider_child == CHILD_GOODS_CATEGORIES:
            yield Request(self.base_url, callback=self.parse)

    def update_goods_detail(self, response):
        # 首页为起始入口
        for goods_model in self.goods_model_list:
            url = goods_model.url
            # print(url) URL规则变更
            # for category in self.start_categories:
            #     if url.find("/"+category+"/products") > 0:
            #         url = url.replace("/"+category + "/products", "/products")
            # if url.find("/collections/products") > 0:
            #     url = url.replace("/collections/products", "/products")
            print(url)
            yield Request(url, dont_filter=True, callback=self.parse, meta={'goods_model': goods_model})

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

    @staticmethod
    def get_product_attr_content(desc_ele, attr_name='Fabric'):
        content = ''
        try:
            # [contains(text(), "{}")]
            xpath = 'div/div[@class="product_collapsible_title"]/span'
            attr_title_ele = desc_ele.xpath('{}[text()="{}"]'.format(xpath, attr_name))
            # [contains(.,text())]
            content_html_ele = attr_title_ele.xpath('parent::div/parent::div/div[2]')
            # http://www.xoxxoo.com/index/index/article/id/280
            content_html = content_html_ele.xpath('string(.)').extract()[0]
            content = content_html.replace('<br>', ' ').replace('\n', '  ').strip()
        except Exception as e:
            pass
        return content

    @staticmethod
    def get_product_schema_text(desc_ele):
        schema_text = ''
        schema_ele = desc_ele.xpath('span')
        if schema_ele:
            schema_text = schema_ele.xpath('string(.)').extract()[0].strip()
        return schema_text

    @staticmethod
    def get_product_image(response: TextResponse) -> str:
        image_url = ''
        ele = response.xpath('//div[@class="product__media media"]/img')
        if ele:
            image_url = ele.xpath('@src').get()
        return "https:" + image_url

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
            goods_model: Goods = response.meta['goods_model']
            print('Response : Goods ID {}  ..  URL: {}'.format(str(goods_model.id), response.url))
            item_goods = GympluscoffeeGoodsItem()
            item_goods['model'] = goods_model
            item_goods['url'] = response.url
            title_ele = response.xpath(self.xpath_product_title)
            item_goods['title'] = title_ele.xpath('text()').get().strip() if title_ele else ''
            if response.status != 200:
                self.mylogger.debug("Warning: " + response.url + " : status = " + str(response.status))
                item_goods['status'] = Goods.STATUS_AVAILABLE
                yield item_goods
                return True

            price = response.xpath("//meta[@property=\"og:price:amount\"]/@content")
            item_goods['price'] = price.get()

            details = {}
            desc_ele = response.xpath(self.xpath_product_desc)
            details['schema'] = self.get_product_schema_text(desc_ele)
            details['details'] = self.get_product_attr_content(desc_ele, 'Details')
            details['fabric'] = self.get_product_attr_content(desc_ele, 'Fabric')
            # print(self.to_chinese(fabric))
            reviews_ele = response.xpath(self.xpath_product_reviews + '/text()')
            reviews_text = ''
            reviews_num = 0
            try:
                reviews_text = reviews_ele.get().strip()
                if reviews_text != 'No reviews':
                    reviews_num = int(reviews_text.replace(',', '').split(' ')[0])
            except AttributeError:
                print(reviews_text)
            item_goods['reviews_num'] = reviews_num
            rating = {}
            if reviews_num > 0:
                for ele in response.xpath(self.xpath_product_rating):
                    rating_key = ele.xpath('@data-rating').get()
                    rating_value = ele.xpath('@data-frequency').get()
                    rating[rating_key] = int(rating_value)
            details['rating'] = rating

            item_goods['details'] = details
            item_goods['image'] = self.get_product_image(response)
            item_goods['image_urls'] = [item_goods['image']]  # 图片管道

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
                            item_sku['image_urls'] = [item_sku['image']]  # 图片下载管道
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
