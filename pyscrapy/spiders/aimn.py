import time

from scrapy.http import TextResponse, Request
from .basespider import BaseSpider
from pyscrapy.items import BaseGoodsItem
import json
from pyscrapy.models.Goods import Goods


class AimnSpider(BaseSpider):

    name = 'aimn'

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
    }

    API_URL = "https://api-v3.findify.io/v3/smart-collection/collections/all-products"
    limit = 24
    api_key = "8f97d0d5-c808-47aa-8499-8aee6533989e"
    uid = "plPzSHFe7SmxqbaS"
    sid = "DbezUFAuq8rKu68J"

    def __init__(self, name=None, **kwargs):
        super(AimnSpider, self).__init__(name=name, **kwargs)
        self.domain = "aimn.co.nz"
        self.base_url = f"https://www.{self.domain}"
        self.allowed_domains.append('api-v3.findify.io')
        # self.allowed_domains.append('baidu.com') 启动URL的域名不需要加入

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
            "filters": [],
            'key': self.api_key,
            'limit': self.limit,
            'slot': "collections/all-products",
            't_client': t_client,
            'user': user
        }
        if offset > 0:
            request_body["offset"] = offset
        request_body = json.dumps(request_body)
        return Request(self.API_URL, callback=self.parse, method='POST', headers=headers, body=request_body,
                       meta=dict(page=page))

    def start_requests(self):
        print('start_requests----------------------')
        yield self.request_goods_list(page=1)

    def parse(self, response: TextResponse, **kwargs):
        meta = response.meta
        page = meta['page']
        # time.sleep(3)
        text = response.text
        json_response = json.loads(text)
        items_list = json_response['items']
        goods_item = BaseGoodsItem()
        for item in items_list:

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

            image = item['image_url']
            # colors_list = item['color']
            price = item['price'][0]
            goods_item['status'] = status
            goods_item['spider_name'] = self.name
            goods_item['price'] = price
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = item['id']
            goods_item['title'] = item['title']
            # url = self.get_site_url(item['product_url']) if 'product_url' in item else ''
            goods_item['url'] = self.get_site_url(item['product_url'])
            goods_item['quantity'] = item['quantity']
            yield goods_item
        print('page {} SUCCESS. response status {} '.format(str(page), str(response.status)))

        if response.status == 200 and items_list:
            yield self.request_goods_list(page+1)
