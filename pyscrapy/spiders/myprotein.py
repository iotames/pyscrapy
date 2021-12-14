from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from pyscrapy.grabs.basegrab import BaseResponse, BaseElement
from Config import Config


class MyproteinSpider(BaseSpider):

    name = 'myprotein'

    base_url = "https://www.myprotein.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1, default 8
        # 'CONCURRENT_REQUESTS': 22,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    goods_list_urls = {
        "mens": "/clothing/mens/view-the-whole-range.list",
        "womens": "/clothing/womens/view-the-whole-range.list",
        "accessories": "/clothing/soft-accessories.list"
    }

    xpath_goods_count = '//p[@class="responsiveProductListHeader_resultsCount"]/text()'
    xpath_last_page = '//a[@class="responsivePaginationButton responsivePageSelector   responsivePaginationButton--last"]/text()'
    xpath_goods_item = '//ul[@class="productListProducts_products"]/li/div[@class="athenaProductBlock"]'

    xpath_goods_overview = '//div[@id="product-description-content-2"]/div/div/p[{}]/text()'  # 1 2 3
    xpath_goods_benefits = '//div[@id="product-description-content-lg-4"]/div/div/ul/li/text()'
    xpath_goods_range = '//div[@class="productDescription_contentWrapper"][1]/div[2]/div/text()'  # 适用范围类别
    xpath_goods_detail_pairs = '//div[@class="productDescription_contentWrapper"][{}]/div[{}]/{}/text()'  # 1 1 span, 1 2 div
    xpath_goods_title = '//div[@class="athenaProductPage_lastColumn"]//h1[@class="productName_title"]/text()'
    xpath_goods_price_text = '//div[@class="athenaProductPage_lastColumn"]//p[@class="productPrice_price "]/text()'
    xpath_goods_price = '//div[@class="athenaProductPage_lastColumn"]//span[@class="productPrice_schema productPrice_priceAmount"]/text()'
    xpath_goods_price_rr_text = '//div[@class="athenaProductPage_lastColumn"]//p[@class="productPrice_rrp"]/text()'
    xpath_goods_price_saving_text = '//div[@class="athenaProductPage_lastColumn"]//p[@class="productPrice_savingAmount"]/text()'

    def get_goods_count(self, response: TextResponse):
        ele = response.xpath(self.xpath_goods_count)
        if ele:
            text = ele.get().strip()
            text_list = text.split(' ')
            count = text_list[0].replace(',', '')
            return int(count)
        return 0

    def get_last_page(self, response: TextResponse) -> int:
        ele = response.xpath(self.xpath_last_page)
        if ele:
            text = ele.get().strip()
            return int(text)
        return 0

    def __init__(self, name=None, **kwargs):
        super(MyproteinSpider, self).__init__(name=name, **kwargs)
        self.domain = self.name + '.com'
        self.base_url = "https://www." + self.domain

    @classmethod
    def get_children_list(cls):
        return [cls.CHILD_GOODS_DETAIL, cls.CHILD_GOODS_LIST]

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for category_name, url in self.goods_list_urls.items():
                url = self.base_url + url
                yield Request(
                    url,
                    callback=self.parse_goods_list,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1, category_name=category_name)
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
            print('goods_list_len : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield self.request_detail(model)
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def request_detail(self, model: Goods):
        return Request(
            self.get_site_url(model.url),
            headers={'referer': self.base_url},
            callback=self.parse_goods_detail_page,
            meta=dict(model=model)
        )

    def parse_goods_detail_page(self, response: TextResponse):
        print('parse_goods_detail_page====================================')

        item = BaseGoodsItem()

        model = response.meta['model']
        page_ele = BaseResponse(response)
        title = page_ele.get_text(self.xpath_goods_title)
        price_text = page_ele.get_text(self.xpath_goods_price_text)
        if price_text:
            price = page_ele.get_text(self.xpath_goods_price)
            item["price_text"] = price_text
            item['price'] = price
            item['status'] = Goods.STATUS_AVAILABLE
        else:
            item['status'] = Goods.STATUS_SOLD_OUT  # '//button[@class="productAddToBasket productAddToBasket-soldOut"]'
        overview = []
        for i in range(1, 6):
            text = page_ele.get_text(self.xpath_goods_overview.format(str(i)))
            if text:
                overview.append(text)

        benefits = []
        for ele in response.xpath(self.xpath_goods_benefits):
            text = ele.get().strip()
            if text:
                benefits.append(text)

        details = json.loads(model.details)

        for par in range(1, 6):
            par_key = response.xpath(self.xpath_goods_detail_pairs.format(str(par), '1', 'span'))
            par_value = response.xpath(self.xpath_goods_detail_pairs.format(str(par), '2', 'div'))
            if par_key and par_value:
                par_key = par_key.get().split(':')[0].strip().lower()
                par_value = par_value.get().strip()
                details[par_key] = par_value

        details['overview'] = overview
        details['benefits'] = benefits
        details['price_rr_text'] = page_ele.get_text(self.xpath_goods_price_rr_text)
        details['price_saving_text'] = page_ele.get_text(self.xpath_goods_price_saving_text)

        item['spider_name'] = self.name
        item["model"] = model
        item['title'] = title

        item['details'] = details
        yield item

    def parse_goods_list(self, response: TextResponse):
        page = response.meta['page']
        category_name = response.meta['category_name']
        print('===========page========' + str(page))
        last_page = self.get_last_page(response)
        goods_items = response.xpath(self.xpath_goods_item)

        for goods in goods_items:
            print('============parse_goods_list=====start=================')
            ele = BaseElement(goods)
            product_id = ele.get_text('span/@data-product-id')
            title = ele.get_text('span/@data-product-title')  # 'a/div/h3/text()'
            brand = ele.get_text('span/@data-product-brand')
            print(brand)
            price_text = ele.get_text('span/@data-product-price')
            print(price_text)
            price = 0
            if price_text:
                price = price_text.split('£')[1]
            image = ele.get_text('div/a/img/@src')
            print(image)
            url = self.get_site_url(ele.get_text('div/a/@href'))
            print(url)
            rating_value_text = ele.get_text('div[@class="athenaProductBlock_rating"]/span[@class="athenaProductBlock_ratingValue"]/text()')
            rating_value = 0
            print(rating_value_text)
            if rating_value_text:
                rating_value = float(rating_value_text)

            review_count_text = ele.get_text('div[@class="athenaProductBlock_rating"]/span[@class="athenaProductBlock_reviewCount"]/text()')
            review_count = 0
            if review_count_text:
                review_count = int(review_count_text)
            print('============parse_goods_list=====end================='+str(page))
            model = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.code == product_id).first()
            details = {'brand': brand, 'rating_value': rating_value}
            if model:
                details = json.loads(model.details)
                details['brand'] = brand
                details['rating_value'] = rating_value
            item = BaseGoodsItem()
            item['spider_name'] = self.name
            item['category_name'] = category_name
            item['model'] = model
            item['image_urls'] = [image]
            item['code'] = product_id
            item['title'] = title
            item['url'] = url
            item['price_text'] = price_text
            item['price'] = price
            item['image'] = image
            item['reviews_num'] = review_count
            item['details'] = details
            print(item)
            yield item

        if page < last_page:
            url = response.url
            next_page = page+1
            if page == 1:
                url = url + "?pageNumber=2"
            else:
                url = url.split('?')[0] + "?pageNumber=" + str(next_page)
            yield Request(
                url,
                callback=self.parse_goods_list,
                meta=dict(page=next_page, category_name=category_name)
            )
