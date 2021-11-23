
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
# from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
# from translate import Translator


class MyproteinSpider(BaseSpider):

    name = 'myprotein'

    base_url = "https://www.myprotein.com"

    # custom_settings = {
    #     # 'DOWNLOAD_DELAY': 3,
    #     # 'RANDOMIZE_DOWNLOAD_DELAY': True,
    #     # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1, default 8
    #     'CONCURRENT_REQUESTS': 16,  # default 16 recommend 5
    # }

    goods_list_urls = [
        "/clothing/mens/view-the-whole-range.list",
        # "/clothing/womens/view-the-whole-range.list",
        # "/clothing/soft-accessories.list"
    ]

    xpath_goods_count = '//p[@class="responsiveProductListHeader_resultsCount"]/text()'
    xpath_last_page = '//a[@class="responsivePaginationButton responsivePageSelector   responsivePaginationButton--last"]/text()'
    xpath_goods_item = '//ul[@class="productListProducts_products"]/li/div[@class="athenaProductBlock"]'
    xpath_goods_code = '@rel'

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

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for url in self.goods_list_urls:
                url = self.base_url + url
                yield Request(
                    url,
                    callback=self.parse_goods_list,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1)
                )
        # TODO 点一次未更新完整，要多点几次。原因未知
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(
                Goods.site_id == self.site_id,
                Goods.updated_at < before_time
            ).all()
            goods_list_len = len(self.goods_model_list)
            print(goods_list_len)
            if goods_list_len > 0:
                yield self.request_detail(0)

    def request_detail(self, model_index: int):
        model = self.goods_model_list[model_index]
        return Request(
            self.get_site_url(model.url),
            headers={'referer': self.base_url},
            callback=self.parse_goods_detail_page,
            meta=dict(model_index=model_index)
        )

    def parse_goods_detail_page(self, response: TextResponse):
        print('parse_goods_detail_page====================================')
        item = response.meta['item']
        try:
            composition = response.xpath("/text()").get().strip()
            fabric = composition.split(":")[1].strip()
            details = item['details']
            details["fabric"] = fabric
            item['details'] = details
        except AttributeError:
            print("AttributeError: =============================================================")
        yield item

    @staticmethod
    def get_product_code(li_id: str):
        id1 = li_id.split("-")
        return id1[1]

    def parse_goods_list(self, response: TextResponse):
        page = response.meta['page']
        print('===========page========' + str(page))
        last_page = self.get_last_page(response)
        goods_items = response.xpath(self.xpath_goods_item)
        for goods in goods_items:
            print('============parse_goods_list=====start=================')
            product_id = goods.xpath('span/@data-product-id').get()
            title = goods.xpath('span/@data-product-title').get().strip()
            # title = goods.xpath('a/div/h3/text()').get().strip()
            brand = goods.xpath('span/@data-product-brand').get()
            print(brand)
            price_text = goods.xpath('span/@data-product-price').get().strip()
            print(price_text)
            price = 0
            if price_text:
                price = price_text.split('£')[1]
            # price_text = goods.xpath('div//span[@class="athenaProductBlock_priceValue"]/text()').get()
            image = goods.xpath('div/a/img/@src').get()
            print(image)
            url = self.get_site_url(goods.xpath('div/a/@href').get())
            print(url)
            rating_value_ele = goods.xpath('div[@class="athenaProductBlock_rating"]/span[@class="athenaProductBlock_ratingValue"]/text()')
            rating_value = 0
            if rating_value_ele:
                print(rating_value_ele.get())
                rating_value = float(rating_value_ele.get())
            review_count_ele = goods.xpath('div[@class="athenaProductBlock_rating"]/span[@class="athenaProductBlock_reviewCount"]/text()')
            review_count = 0
            if review_count_ele:
                review_count = int(review_count_ele.get())
            print(rating_value)
            print(review_count)
            print('============parse_goods_list=====end================='+str(page))
            model = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.code == product_id).first()
            item = BaseGoodsItem()
            item['spider_name'] = self.name
            item['model'] = model
            item['image_urls'] = [image]
            item['code'] = product_id
            item['title'] = title
            item['url'] = url
            item['price_text'] = price_text
            item['price'] = price
            item['image'] = image
            item['reviews_num'] = review_count
            item['details'] = {'brand': brand, 'rating_value': rating_value}
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
                meta=dict(page=next_page)
            )
