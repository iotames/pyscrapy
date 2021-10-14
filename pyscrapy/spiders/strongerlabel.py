import time

from scrapy.http import TextResponse, request
from .basespider import BaseSpider
import json


class StrongerlabelSpider(BaseSpider):
    name: str = 'strongerlabel'

    sl_uid: str
    sl_sid: str
    sl_key: str

    def __init__(self, name=None, **kwargs):
        super(StrongerlabelSpider, self).__init__(name=name, **kwargs)
        self.start_urls = [
            "https://api-v3.findify.io/v3/search"
            # 'https://www.strongerlabel.com/'
        ]
        self.sl_uid = "7294d35d-e23f-4406-98ed-7ea9ee6c099b"
        self.sl_sid = '00a32083-7a31-4ebc-9654-1a172df0c9c0'
        self.sl_key = '16d7a766-26a5-4394-9fac-846d0404f434'

    def start_requests(self):
        t_client = int(time.time()*1000)
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
        for url in self.start_urls:
            user = {'uid': self.sl_uid, 'sid': self.sl_sid}
            request_body = {
                'user': user,
                't_client': t_client,
                'key': self.sl_key,
                "filters": [
                    {"name": "market_stock_1", "type": "range", "values": [{"from": -1000}], "action": "include"}
                ],
                "limit": 20,
                "offset": 40,
                "q": ""
            }
            request_body = json.dumps(request_body)
            yield request.Request(
                url,
                callback=self.parse,
                method='POST',
                headers=headers,
                body=request_body
            )

    def parse(self, response: TextResponse, **kwargs):
        text = response.text
        json_response = json.loads(text)
        items_list = json_response['items']
        output = ''
        for item in items_list:
            if 'category' in item:
                categories = []
                for categoryl in item['category']:
                    categories.append(categoryl['category1'])
                print(categories)
            created_at = int(item['created_at']/1000)
            print(created_at)
            # stickers: { in-stock: true, out-of-stock: false}
            print(item['stickers'])
            price = item['price'][0]
            image = item['image_url']
            output_format = "id={} title={} {}USD url={} quantity={} image={} \r\n"
            url = item['product_url'] if 'product_url' in item else 'unknown========================='
            output = output + output_format.format(item['id'], item['title'], price, url, item['quantity'], image)
        self.mylogger.debug(output)
        self.logger.debug(text)
