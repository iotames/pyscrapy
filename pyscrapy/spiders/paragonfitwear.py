from scrapy.http import TextResponse, Request
from pyscrapy.spiders.basespider import BaseSpider
from pyscrapy.items import BaseGoodsItem
import json
from pyscrapy.models.Goods import Goods
from Config import Config
from pyscrapy.enum.spider import *


class ParagonfitwearSpider(BaseSpider):

    name = NAME_PARAGONFITWEAR

    custom_settings = {
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    def __init__(self, name=None, **kwargs):
        super(ParagonfitwearSpider, self).__init__(name=name, **kwargs)

    # @staticmethod
    # def get_image_url(url: str, size=720) -> str:
    #     original = '_large.jpg'
    #     if url.find(original) > -1:
    #         url = url.replace(original, f"_{str(size)}x.jpg")
    #     return url
    
    def request_goods_list(self, page: int) -> Request:
        url = self.get_site_url("/collections/all")
        if page > 1:
            url += f"{url}?page={str(page)}"
        return Request(url, self.parse_goods_list, meta=dict(page=page))

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST:
            yield self.request_goods_list(1)
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            def get_request(model: Goods) -> str:
                return f"{model.url}.js"
            request_list = self.request_list_goods_detail(get_request)
            for req in request_list:
                yield req
    
    def parse_goods_list(self, response: TextResponse):
        
        json_data_ele = response.xpath("//script[@type=\"application/ld+json\"]/text()")
        if len(json_data_ele) == 2:
            json_data_text = json_data_ele.extract()[1].strip()
            print(json_data_text)
            json_data = json.loads(json_data_text)
            item_list = json_data["itemListElement"]
            for goods in item_list:
                goods_item = BaseGoodsItem()
                goods_item['spider_name'] = self.name
                goods_item['title'] = goods['name']
                goods_item['url'] = goods['url']
                yield goods_item
            if len(item_list) == 100:
                meta = response.meta
                page = meta.get("page")
                yield self.request_goods_list(page+1)
    
    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        goods_model = meta['goods_model']
        json_data = response.json()
        status = Goods.STATUS_AVAILABLE if json_data['available'] else Goods.STATUS_UNAVAILABLE
        category_name = json_data["type"]
        title = json_data['title']
        code = str(json_data['id'])
        price = json_data['price'] / 100
        image = json_data["images"][0]
        image = f"https:{image}"
        quantity = 0
        for variant in json_data['variants']:
            quantity += variant['inventory_quantity']
        goods_item = BaseGoodsItem()
        goods_item['model'] = goods_model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        goods_item['image'] = image
        goods_item['code'] = code
        goods_item['title'] = title
        goods_item['image_urls'] = [image]
        # goods_item['url'] = response.url
        goods_item['price'] = price
        # goods_item['price_text'] = price_text
        # goods_item['reviews_num'] = reviews_num
        goods_item['status'] = status
        goods_item['quantity'] = quantity
        yield goods_item
