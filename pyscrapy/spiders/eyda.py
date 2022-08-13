from scrapy.http import TextResponse, Request
from .basespider import BaseSpider
from pyscrapy.items import BaseGoodsItem
from scrapy.selector import Selector
from pyscrapy.models.Goods import Goods
from Config import Config
from pyscrapy.enum.spider import *


class EydaSpider(BaseSpider):

    name = NAME_EYDA

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    def get_price_text(self, price):
        if self.domain == "eyda.com":
            return f"€{price}"
        if self.domain == "eyda.dk":
            return f"{price} kr."

    def __init__(self, name=None, **kwargs):
        super(EydaSpider, self).__init__(name=name, **kwargs)
        self.base_url = f"https://{self.domain}"
        self.image_referer = self.base_url + "/"
        # self.allowed_domains.append('api-v3.findify.io')

    def request_goods_list(self, page: int) -> Request:
        url = f"https://eyda.com/collections/all?page={str(page)}&view=data"
        return Request(url, self.parse_goods_list, meta=dict(page=page))

    def start_requests(self):
        yield self.request_goods_list(page=1)

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        goods_items_list = response.json()
        for item in goods_items_list:
            # published_at: "2021-01-28 11:44:14 +0100"

            desc_html = item['description']
            select = Selector(text=desc_html)
            composition_ele = select.xpath('//p[contains(text(), "% ")]')
            clen = len(composition_ele)
            composition_text = ""
            if clen > 0:
                if clen == 1:
                    composition_text = composition_ele[0].xpath("text()").get()
                else:
                    for com_ele in composition_ele:
                        text = com_ele.xpath("text()").get()
                        if len(text) < 50:
                            composition_text = text

            status = Goods.STATUS_AVAILABLE if item['available'] else 0
            image = "https:" + item['images'][0]['src']
            price = item['price'] / 100
            spu = item['handle']
            url = self.get_site_url(f"/products/{spu}")
            code = item['id']
            title = item['title']
            category_name = item['type']
            colors_list = item['color_values'] if 'color_values' in item else []
            quantity = 0
            sku_info_list = []
            for sku_item in item['variants']:
                # sku title quantity price option1 option2 image
                quantity += sku_item['quantity']
                sku_info = {
                    'title': sku_item['title'],
                    'quantity': sku_item['quantity'],
                    'image': "https:" + sku_item['image'],
                    'price': sku_item['price'] / 100
                }
                sku_info_list.append(sku_info)
            details = {'composition_text': composition_text, 'colors_list': colors_list, 'sku_info_list': sku_info_list}
            goods_item = BaseGoodsItem()
            goods_item['status'] = status
            goods_item['asin'] = spu
            goods_item['spider_name'] = self.name
            goods_item['price'] = price
            goods_item["price_text"] = self.get_price_text(price)
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = code
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['category_name'] = category_name
            goods_item['quantity'] = quantity
            goods_item['details'] = details
            yield goods_item
        if response.status == 200 and goods_items_list:
            yield self.request_goods_list(page+1)

    def parse_goods_detail(self, response: TextResponse):
        pass

