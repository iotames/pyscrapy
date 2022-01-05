import re
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from urllib.parse import urlencode
import base64
import html


class JomasportSpider(BaseSpider):

    name = 'joma-sport'

    base_url = "https://www.joma-sport.com"

    api_url = "https://www.joma-sport.com/ka/ajax.php"

    categories_list = [
        {"name": "clothes-man", "url": "https://www.joma-sport.com/en/clothes-man"},
        {"name": "clothes-woman", "url": "https://www.joma-sport.com/en/clothes-woman"},
    ]
    api_key = "0VJCRZMBZ1ISBYJOFFHO8Z3XZ6O60KBY"

    categories_info = {}  # start = 0 sz = 24
    # b'{0:"products",1:"en/clothes-woman",2:"",3:"/en/clothes-woman",4:"M56DUKTUDBHDGRVP8RR8N98Z4GXXG1M5",5:4}'
    # {0: "products", 1: "en/clothes-woman", 2: "", 3: "/en/clothes-woman", 4: "M56DUKTUDBHDGRVP8RR8N98Z4GXXG1M5", 5: 2}
    # {0:"products",1:"en/clothes-man",2:"",3:"/en/clothes-man",4:"E6GFF7Z0KV6VUY3JIZ1RP83CDGTD6YRX",5:2}

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'COOKIES_ENABLED': True,
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    def __init__(self, name=None, **kwargs):
        super(JomasportSpider, self).__init__(name=name, **kwargs)

    def request_goods_list(self, category_name: str, page: int):
        referer = f"{self.base_url}/en/{category_name}"
        headers = {
            'referer': referer,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        meta = {'page': page, 'category_name': category_name}
        if page == 1:
            self.categories_info[category_name] = dict()
            req_url = ""
            for cat in self.categories_list:
                if cat["name"] == category_name:
                   req_url = cat["url"]
            if not req_url:
                raise RuntimeError("request url 不能为空")
            return Request(req_url, callback=self.parse_goods_list, meta=meta)

        data_cache = self.categories_info[category_name]['data_cache']
        cookies = self.categories_info[category_name]['cookies']
        data = {0: "products", 1: f"en/{category_name}", 2: "", 3: f"/en/{category_name}", 4: data_cache, 5: page}
        json_data_str = json.dumps(data, separators=(',', ':'))
        print(json_data_str)
        token = str(base64.encodebytes(json_data_str.encode('utf8')), 'utf-8').replace('\n', '')
        print(token)
        post_data = "p=" + token
        print(post_data)
        return Request(
            self.api_url,
            method="POST",
            headers=headers,
            body=post_data,
            cookies=cookies,
            callback=self.parse_goods_list,
            meta=meta
        )

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for category in self.categories_list:
                name = category.get("name")
                yield self.request_goods_list(name, 1)
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
            print('=======goods_list_len============ : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield Request(self.get_site_url(model.url), headers={'referer': self.base_url + "/AU/"},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    goods_list_count = 0

    def is_last_page(self, start: int, product_total: int) -> bool:
        return False

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        category_name = meta["category_name"]
        page = meta['page']
        print(page)
        print(category_name)
        if page == 1:
            data_cache = response.xpath('//div[@id="pagination_trigger"]/@data-cache').get()
            print(data_cache)
            self.categories_info[category_name]['data_cache'] = data_cache
            self.categories_info[category_name]['cookies'] = {}
            cookie_str: str = response.headers['set-cookie'].decode()
            print(cookie_str)
            for cookie_pair in cookie_str.split(';'):
                ck = cookie_pair.strip().split('=')
                # self.cookies[ck[0]] = ck[1]
                self.categories_info[category_name]['cookies'][ck[0]] = ck[1]
        print('=======cookies===and===data_cache====')
        print(self.categories_info[category_name])

        if page > 1:
            # html_text = html.unescape(response.text)
            print(response.text.replace("\\t", '').replace("\\n", '').replace("\\", ''))
        # start = self.categories_info[category_name]["start"]
        # print('========================start======{}=={}==='.format(category_name, str(start)))
        # if start == 0:
        #     product_total = int(response.xpath('//span[@class="total-product-count"]/text()').extract()[0])
        #     self.categories_info[category_name]["product_total"] = product_total
        # else:
        #     product_total = self.categories_info[category_name]["product_total"]

        # xpath = '//li[@class="grid-tile columns"]/div[@class="product-tile"]'
        # eles = response.xpath(xpath)
        # for ele in eles:
        #     goods_item = BaseGoodsItem()
        #     goods_item['spider_name'] = self.name
        #     goods_item['url'] = url
        #     goods_item['code'] = code
        #     goods_item['asin'] = spu
        #     goods_item['price'] = price
        #     goods_item['price_text'] = price_text
        #     goods_item['title'] = title
        #     goods_item['image'] = image
        #     goods_item['image_urls'] = [image]
        #     goods_item['category_name'] = category_name
        #     goods_item['details'] = {'color_num': color_num}
        #     yield goods_item

        # if not self.is_last_page(start, product_total):
        if page < 3:
            print('==========next==' + str(page+1))
            yield self.request_goods_list(category_name, page+1)

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        features_list = []
        features_eles = response.xpath('//ul[@class="product-tab-list"]/li')
        for feature_ele in features_eles:
            features_list.append(feature_ele.xpath("text()").get().strip())

        composition_ele = response.xpath('//div[@class="product-tab-title"][contains(text(), "Composition")]/parent::div/div[@class="product-tab-value"]/text()')
        composition_text = composition_ele.get().strip() if composition_ele else ""

        goods_item = BaseGoodsItem()
        goods_item['spider_name'] = self.name
        goods_item['model'] = model
        goods_item['url'] = response.url
        details = json.loads(model.details)
        details["features_list"] = features_list
        details["composition"] = composition_text
        goods_item['details'] = details
        yield goods_item


if __name__ == '__main__':
    # strr = '{0:"products",1:"en/clothes-woman",2:"",3:"/en/clothes-woman",4:"M56DUKTUDBHDGRVP8RR8N98Z4GXXG1M5",5:2}'
    # print(base64.encodebytes(strr.encode('utf-8')))
    # encode = "ezA6InByb2R1Y3RzIiwxOiJlbi9jbG90aGVzLXdvbWFuIiwyOiIiLDM6Ii9lbi9jbG90aGVzLXdvbWFuIiw0OiJNNTZEVUtUVURCSERHUlZQOFJSOE45OFo0R1hYRzFNNSIsNTo0fQ=="
    # decode = base64.decodebytes(encode.encode('utf8'))
    # print(decode)
    encode_heml = "<div id=\"pagination_trigger\" data-page=\"2\" data-pagehash=\"b07\" data-cache=\"E6GFF7Z0KV6VUY3JIZ1RP83CDGTD6YRX\"><\/div>"
    print(encode_heml.replace('\t', '').replace('\n', '').replace('\\', ''))

