import time

from scrapy.http import TextResponse, request
from .basespider import BaseSpider
from ..items import StrongerlabelGoodsItem
import json


class StrongerlabelSpider(BaseSpider):
    name: str = 'strongerlabel'

    sl_uid: str
    sl_sid: str
    sl_key: str

    def __init__(self, name=None, **kwargs):
        super(StrongerlabelSpider, self).__init__(name=name, **kwargs)
        self.allowed_domains.append('api-v3.findify.io')
        self.start_urls = [
            "https://api-v3.findify.io/v3/search"
            # 'https://www.strongerlabel.com/'
        ]
        self.sl_uid = "7294d35d-e23f-4406-98ed-7ea9ee6c099b"
        self.sl_sid = '00a32083-7a31-4ebc-9654-1a172df0c9c0'
        self.sl_key = '16d7a766-26a5-4394-9fac-846d0404f434'

    def start_requests(self):
        for url in self.start_urls:
            yield self.request_goods_list(url, offset=0)

    def request_goods_list(self, url, offset):
        t_client = int(time.time() * 1000)
        headers = {
            # 'content-length': 608,
            'content-type': 'application/json',  # content-type 必填
            # 'origin': 'https://www.strongerlabel.com',
            # 'referer': 'https://www.strongerlabel.com/',
            # 'sec-ch-ua': "\"Chromium\";v=\"94\", \"Google Chrome\";v=\"94\", \";Not A Brand\";v=\"99\"",
            # 'sec-ch-ua-mobile': '?0',
            # 'sec-ch-ua-platform': "Linux",
            # 'user-agent': '',
            'x-key': self.sl_key  # x-key 必填
        }
        user = {'uid': self.sl_uid, 'sid': self.sl_sid}
        request_body = {
            'user': user,
            't_client': t_client,
            'key': self.sl_key,
            "filters": [
                {"name": "market_stock_1", "type": "range", "values": [{"from": -1000}], "action": "include"}
            ],
            "limit": 20,
            "offset": offset,
            "q": ""
        }
        request_body = json.dumps(request_body)
        return request.Request(
                url,
                callback=self.parse,
                method='POST',
                headers=headers,
                body=request_body,
                meta={'offset': offset}
            )

    def parse(self, response: TextResponse, **kwargs):
        time.sleep(3)
        text = response.text
        json_response = json.loads(text)
        items_list = json_response['items']
        output = ''
        goods_item = StrongerlabelGoodsItem()
        for item in items_list:
            categories = []
            if 'category' in item:
                for categoryl in item['category']:
                    categories.append(categoryl['category1'])
            goods_item['categories'] = categories
            created_at = int(item['created_at']/1000)
            goods_item['created_at'] = created_at
            if 'stickers' in item:
                goods_item['stickers'] = item['stickers']  # stickers: { in-stock: true, out-of-stock: false}
                for stkey, stkvalue in item['stickers'].items():
                    if stkvalue and stkey != 'in-stock':
                        self.mylogger.debug('stickers!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! TRUE ' + stkey)

            price = item['price'][0]
            goods_item['price'] = price
            goods_item['image'] = item['image_url']
            goods_item['code'] = item['id']
            goods_item['title'] = item['title']
            url = item['product_url'] if 'product_url' in item else ''
            goods_item['url'] = url
            # print(item['title'] + " : " + url)
            quantity = item['quantity']
            goods_item['quantity'] = quantity
            yield goods_item

        offset = response.meta['offset']
        print('offset {} SUCCESS. response status {} '.format(str(offset), str(response.status)))

        if offset < 500:
            offset += 20
            yield self.request_goods_list(response.url, offset)
