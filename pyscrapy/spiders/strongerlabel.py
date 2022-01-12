import time

from scrapy.http import TextResponse, Request
from .basespider import BaseSpider
from ..items import StrongerlabelGoodsItem
import json
from pyscrapy.models.Goods import Goods
from Config import Config


class StrongerlabelSpider(BaseSpider):

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    name: str = 'strongerlabel'

    base_api_url = "https://api-v3.findify.io"

    sl_uid: str
    sl_sid: str
    sl_key: str

    def __init__(self, name=None, **kwargs):
        print('init---------------------------------------')
        super(StrongerlabelSpider, self).__init__(name=name, **kwargs)
        self.image_referer = self.base_url + "/"
        print('after super-------------------------')
        print(self.mylogger)
        print(self.log_id)
        self.allowed_domains.append('api-v3.findify.io')
        # self.allowed_domains.append('baidu.com') 启动URL的域名不需要加入
        print(self.allowed_domains)
        self.sl_uid = "7294d35d-e23f-4406-98ed-7ea9ee6c099b"
        self.sl_sid = 'b35f55f7-6ba2-482a-b0f1-bf5f5864e78d'
        self.sl_key = '16d7a766-26a5-4394-9fac-846d0404f434'

    @staticmethod
    def get_image_url(url: str) -> str:
        pre_url = 'https://www.strongerlabel.com/imgproxy/preset:sharp/resize:fit:320/gravity:nowe/quality:70/plain/'
        return pre_url + url

    def start_requests(self):
        print('start_requests----------------------')
        start_url = "https://www.baidu.com"
        yield Request(start_url, callback=self.request_goods_list, cb_kwargs={'url': '', 'offset': -1})

    def request_goods_list(self, response: TextResponse, url='', offset=-1):
        print('url={}, offset={}'.format(response.url, str(offset)))
        if offset == -1:
            url = self.base_api_url + "/v3/search"
            offset = 0
        t_client = int(time.time() * 1000)
        headers = {
            # 'content-length': 608,
            'content-type': 'application/json',  # content-type 必填
            'origin': 'https://www.strongerlabel.com',
            'referer': 'https://www.strongerlabel.com/',
            'sec-ch-ua': "\"Chromium\";v=\"94\", \"Google Chrome\";v=\"94\", \";Not A Brand\";v=\"99\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Linux",
            'user-agent': self.USER_AGENT,
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
        return Request(
                url,
                callback=self.parse,
                method='POST',
                headers=headers,
                body=request_body,
                meta={'offset': offset}
            )

    def parse(self, response: TextResponse, **kwargs):
        # time.sleep(3)
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

            # created_at = int(item['created_at']/1000)
            # goods_item['created_at'] = created_at

            status = Goods.STATUS_AVAILABLE
            if 'stickers' in item:
                # stickers: { in-stock: true, out-of-stock: false}
                if ('out-of-stock' in item['stickers']) and (item['stickers']['out-of-stock'] is True):
                    status = Goods.STATUS_SOLD_OUT
                for stkey, stkvalue in item['stickers'].items():
                    if stkvalue and stkey != 'in-stock':
                        # TODO stickers 包含多个标签 待发现
                        self.mylogger.debug('stickers!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! TRUE ' + stkey)

            price = item['price'][0]
            image = self.get_image_url(item['image_url'])
            goods_item['status'] = status
            goods_item['price'] = price
            goods_item['image'] = image
            goods_item['code'] = item['id']
            goods_item['title'] = item['title']
            url = item['product_url'] if 'product_url' in item else ''
            goods_item['url'] = url
            # print(item['title'] + " : " + url)
            quantity = item['quantity']
            goods_item['quantity'] = quantity
            goods_item['image_urls'] = [image]
            yield goods_item

        offset = response.meta['offset']
        print('offset {} SUCCESS. response status {} '.format(str(offset), str(response.status)))

        if response.status == 200 and items_list:
            offset += 20
            yield self.request_goods_list(response, response.url, offset)
