from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import SweatybettyGoodsItem
from ..models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
# from translate import Translator


class SweatybettySpider(BaseSpider):

    name = 'sweatybetty'

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS': 1,  # 5
    }

    goods_model_list: list
    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    spider_child = CHILD_GOODS_LIST
    goods_list_url = "/shop?start={}&sz=36&format=ajax"  # 0 34 70 106 142

    xpath_goods_list_item = "//ul[@id=\"search-result-items\"]/li[contains(@id, \"productlist-\")]"

    xpath_goods_image = "div/div[@class=\"product-image  \"]/a/img"  # @data-src
    xpath_goods_url = "div/div[@class=\"product-image  \"]/a"  # @href
    xpath_goods_title = "div/div[@class=\"product-tile-details\"]/div[@class=\"product-title\"]/div[@class=\"product-name-grade-wrap\"]/div[@class=\"product-name\"]/a"
    xpath_goods_price = "div/div[@class=\"product-tile-details\"]/div[@class=\"product-pricing\"]/div[@class=\"product-price\"]"  # @data-price-sales  text()
    # xpath_goods_rating = "div/div[@class='product-tile-details']/div[@class='product-rating']/div/div/a/div[@class='bv_numReviews_component_container']"

    def __init__(self, name=None, **kwargs):
        super(SweatybettySpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        self.allowed_domains.append("api.bazaarvoice.com")

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            yield Request(
                self.base_url+self.goods_list_url.format(str(0)),
                callback=self.parse_goods_list,
                headers=dict(referer="https://www.sweatybetty.com/shop?start=34&sz=36&format=ajax"),
                meta=dict(start=0)
            )

    @staticmethod
    def get_product_code(li_id: str):
        id1 = li_id.split("-")
        id2 = id1[1]
        id3 = id2.split("_")
        return id3[0]

    def parse_goods_list(self, response: TextResponse, **kwargs):
        start = response.meta['start']
        print(start)
        next_start = start + 36
        if start == 0:
            next_start = 34
        goods_li_eles = response.xpath(self.xpath_goods_list_item)
        print(len(goods_li_eles))
        i = 0
        for ele in goods_li_eles:
            item = SweatybettyGoodsItem()
            li_id = ele.xpath("@id").get()
            code = self.get_product_code(li_id)
            model = self.db_session.query(Goods).filter(Goods.code == code).first()
            print(code)
            image = ele.xpath(self.xpath_goods_image + "/@data-src").get() + "&fmt=webp"
            print(image)
            url = ele.xpath(self.xpath_goods_url + "/@href").get()
            print(url)
            title = ele.xpath(self.xpath_goods_title + "/text()").get().strip()
            print(title)
            price_text = ele.xpath(self.xpath_goods_price + "/span[1]/text()").get().strip()
            print(price_text)

            # rating = ele.xpath(self.xpath_goods_rating + "/meta/@content").get()
            # print(rating)

            try:
                price = ele.xpath(self.xpath_goods_price + "/span[1]/@data-price-sales").get().strip()
                print(price)
            except AttributeError as e:
                try:
                    print(e)
                    price = ele.xpath(self.xpath_goods_price + "/span[2]/@data-price-sales").get().strip()
                    print(price)
                    price_text = ele.xpath(self.xpath_goods_price + "/span[2]/text()").get().strip()
                    print(price_text)
                except AttributeError:
                    continue
            item["model"] = model
            item["image_urls"] = [image]
            item["code"] = code
            item["title"] = title
            item["url"] = url
            item["image"] = image
            item["price"] = price
            yield item
            i += 1
            print("=========================end======")
        print(i)
        if next_start < 1150:
            yield Request(self.base_url+self.goods_list_url.format(str(next_start)), callback=self.parse_goods_list, meta=dict(start=next_start))
