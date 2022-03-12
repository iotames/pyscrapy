import time

from scrapy.http import TextResponse, Request
from .basespider import BaseSpider
from pyscrapy.items import BaseGoodsItem
import json
from pyscrapy.models.Goods import Goods
from Config import Config
from pyscrapy.enum.spider import *
import re


class AimnSpider(BaseSpider):

    name = NAME_AIMN

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    API_URL = "https://api-v3.findify.io/v3/smart-collection/collections/all-products"
    limit = 24
    filters = []
    slot = "collections/all-products"
    # www.aimn.com: fd978d93-b87c-4c25-8db1-f29de51ee6bf
    # aimn.co.nz: 8f97d0d5-c808-47aa-8499-8aee6533989e
    api_key = "fd978d93-b87c-4c25-8db1-f29de51ee6bf"
    # www.aimn.com: 6Obj6nq1x1hkx8fC
    # aimn.co.nc: plPzSHFe7SmxqbaS
    uid = "6Obj6nq1x1hkx8fC"
    # www.aimn.com: yZsxIgaJZWaHbnb7
    # aimn.co.nz: DbezUFAuq8rKu68J
    sid = "yZsxIgaJZWaHbnb7"

    def __init__(self, name=None, **kwargs):
        super(AimnSpider, self).__init__(name=name, **kwargs)
        # aimn.co.nz
        self.domain = "aimn.com"
        self.base_url = f"https://www.{self.domain}"
        self.image_referer = self.base_url + "/"
        self.allowed_domains.append('api-v3.findify.io')

    @staticmethod
    def get_image_url(url: str, size=720) -> str:
        original = '_large.jpg'
        if url.find(original) > -1:
            url = url.replace(original, f"_{str(size)}x.jpg")
        return url

    def request_goods_list(self, page: int):
        offset = (page - 1) * self.limit

        t_client = int(time.time() * 1000)
        headers = {
            # 'content-length': 608,
            'content-type': 'application/json',  # content-type 必填
            'origin': self.base_url,
            'referer': self.base_url + '/',
            'sec-ch-ua': "\"Chromium\";v=\"94\", \"Google Chrome\";v=\"94\", \";Not A Brand\";v=\"99\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Linux",
            'user-agent': self.USER_AGENT,
            'x-key': self.api_key  # x-key 必填
        }
        user = {'uid': self.uid, 'sid': self.sid, 'exist': True, 'persist': False}
        request_body = {
            "filters": self.filters,
            'key': self.api_key,
            'limit': self.limit,
            'slot': self.slot,
            't_client': t_client,
            'user': user
        }
        if offset > 0:
            request_body["offset"] = offset
        request_body = json.dumps(request_body)
        return Request(self.API_URL, callback=self.parse, method='POST', headers=headers, body=request_body,
                       meta=dict(page=page))

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST:
            yield self.request_goods_list(page=1)
        if self.spider_child == CHILD_GOODS_DETAIL:
            request_list = self.request_list_goods_detail()
            for req in request_list:
                yield req

    statuses = {
        'InStock': Goods.STATUS_AVAILABLE,
        'SoldOut': Goods.STATUS_SOLD_OUT,
        'OutOfStock': Goods.STATUS_SOLD_OUT,
        'Discontinued': Goods.STATUS_UNAVAILABLE
    }

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        goods_model = meta['goods_model'] if 'goods_model' in meta else None
        re_rule0 = r"\"Viewed Product\",(.+?)\);"
        re_info0 = re.findall(re_rule0, response.text)
        info0 = json.loads(re_info0[0])
        code = info0['productId']
        price = info0['price']
        currency = info0['currency']
        price_text = price + currency
        category_name = info0['category']

        xpath_json = '//script[@type="application/ld+json"]/text()'
        json_product_text = response.xpath(xpath_json)[0].get()
        # print('======json_product_text===========')
        # print(json_product_text)
        p_info = json.loads(json_product_text, strict=False)
        print(p_info)
        title = p_info['name']
        url = p_info['url']
        # sku_code = p_info['sku']  # 140003-011
        desc = p_info['description']
        # image_text: str = p_info['image'][0]
        # image_text = image_text.split('?')[0]
        # last_str = image_text.split('_')[-1]
        # img_ext = last_str.split('.')[-1]  # jpg gif
        # image = image_text.replace(last_str, '200x.' + img_ext)
        origin_price_text = ""
        origin_price_ele = response.xpath('//span[@class="product__price product__price--compare"]/text()')
        if origin_price_ele:
            origin_price_text = origin_price_ele.extract()[0]
        print("-------origin_price_text------------" + origin_price_text)
        status = Goods.STATUS_UNAVAILABLE
        offers = p_info['offers']

        for sku in offers:
            """
            {
                "@type" : "Offer","sku": "140003-011","availability" : "http://schema.org/InStock",
                "price" : "68.0", "priceCurrency" : "USD",
                "url" : "https://shefit.com/products/boss-leggings-conquer?variant=38474305700009"
            }
            """
            # price = sku['price']
            # price_text = price + sku['priceCurrency']
            status_text = sku['availability'].split('/')[-1]
            if status_text == 'InStock':
                status = self.statuses[status_text]

        details = {
            # 'sku_list': sku_list,
            'desc': desc,
            'origin_price_text': origin_price_text,
        }
        goods_item = BaseGoodsItem()
        goods_item['model'] = goods_model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        # goods_item['image'] = image
        goods_item['code'] = code
        goods_item['title'] = title
        # goods_item['image_urls'] = [image]
        goods_item['url'] = response.url
        goods_item['price'] = price
        goods_item['price_text'] = price_text
        # goods_item['reviews_num'] = reviews_num
        goods_item['status'] = status
        goods_item['details'] = details
        # goods_item['quantity'] = quantity
        yield goods_item

    def parse(self, response: TextResponse, **kwargs):
        meta = response.meta
        page = meta['page']
        # time.sleep(3)
        text = response.text
        json_response = json.loads(text)
        items_list = json_response['items']
        goods_item = BaseGoodsItem()
        for item in items_list:
            if 'product_url' not in item:
                continue
            # categories = []
            # if 'category' in item:
            #     for categoryl in item['category']:
            #         categories.append(categoryl['category1'])
            # goods_item['categories'] = categories

            status = Goods.STATUS_AVAILABLE
            stickers_list = ['in-stock', 'out-of-stock']
            if 'stickers' in item:
                # stickers: { in-stock: true, out-of-stock: false}
                if ('out-of-stock' in item['stickers']) and (item['stickers']['out-of-stock'] is True):
                    status = Goods.STATUS_SOLD_OUT
                for stkey, stkvalue in item['stickers'].items():
                    if stkey not in stickers_list:
                        # TODO stickers 包含多个标签 待发现
                        self.mylogger.debug('stickers has =============== ' + stkey)

            image = self.get_image_url(item['image_url'])
            price = item['price'][0]
            goods_item['status'] = status
            goods_item['spider_name'] = self.name
            goods_item['price'] = price
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = item['id']
            goods_item['title'] = item['title']
            goods_item['url'] = self.get_site_url(item['product_url'])
            goods_item['quantity'] = item['quantity']
            yield goods_item
        print(f"===current_page===item_len===status==={str(page)}==={str(len(items_list))}==={str(response.status)}==")

        if response.status == 200 and items_list:
            yield self.request_goods_list(page+1)
