from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
import base64
from scrapy.selector import Selector


class JomasportSpider(BaseSpider):

    name = 'joma-sport'

    base_url = "https://www.joma-sport.com"

    api_url = "https://www.joma-sport.com/ka/ajax.php"

    categories_list = [
        {"name": "clothes-man", "url": "https://www.joma-sport.com/en/clothes-man"},
        {"name": "clothes-woman", "url": "https://www.joma-sport.com/en/clothes-woman"},
    ]

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
        token = str(base64.encodebytes(json_data_str.encode('utf8')), 'utf-8').replace('\n', '')
        post_data = "p=" + token

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
        # https://zhuanlan.zhihu.com/p/87963596
        xpath_goods_list = '//div[contains(@class, "product")]'
        meta = response.meta
        category_name = meta["category_name"]
        page = meta['page']
        print(page)
        print(category_name)
        xpath_data_cache = '//div[@id="pagination_trigger"]/@data-cache'
        eles = []
        if page > 1:
            html_text = response.text.replace("\\t", ' ').replace("\\n", ' ').replace("\\", '').strip("\"")
            selector = Selector(text=html_text)
            data_cache = selector.xpath(xpath_data_cache).get()
            print('============page==={}===cache=={}'.format(str(page), data_cache))
            print(data_cache)
            print('===========body=======begin')
            # print(html_text)
            print('===========body==========end')
            eles = selector.xpath(xpath_goods_list)
        else:
            data_cache = response.xpath(xpath_data_cache).get()
            print(data_cache)
            self.categories_info[category_name]['data_cache'] = data_cache
            self.categories_info[category_name]['cookies'] = {}
            cookie_str: str = response.headers['set-cookie'].decode()
            print(cookie_str)
            for cookie_pair in cookie_str.split(';'):
                ck = cookie_pair.strip().split('=')
                self.categories_info[category_name]['cookies'][ck[0]] = ck[1]
            eles = response.xpath(xpath_goods_list)

        print('=======cookies===and===data_cache====')
        print(self.categories_info[category_name])

        count_goods = 0
        for goods_ele in eles:
            url = goods_ele.xpath('a/@href').get()
            if not url:
                continue
            print(url)
            code = goods_ele.xpath('a/@data-product').get()
            print(code)
            image = goods_ele.xpath('a/img[1]/@data-src').get()
            print(image)
            title = goods_ele.xpath('div[@class="datasheet"]//h2/text()').get()
            print(title)
            price_text = goods_ele.xpath('div[@class="datasheet"]//div[@class="price"]/span/text()').get()
            print(price_text)
            price = price_text.split(' ')[0] if price_text else 0

            goods_colors_ele = goods_ele.xpath('div[@class="datasheet"]//div[@class="slides"]/button')
            colors_num = len(goods_colors_ele)
            colors_list = []
            for color_ele in goods_colors_ele:
                color_url = color_ele.xpath('@data-href').get()
                color_code = color_ele.xpath('@data-product').get()
                color_image = color_ele.xpath('@data-main').get()
                colors_list.append({'url': color_url, 'code': color_code, 'image': color_image})
            details = {'colors_num': colors_num, 'colors_list': colors_list}
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['url'] = url
            goods_item['code'] = code
            # goods_item['asin'] = spu
            goods_item['price'] = price
            goods_item['price_text'] = price_text
            goods_item['title'] = title
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['category_name'] = category_name
            goods_item['details'] = details
            yield goods_item

            count_goods += 1

        if "product_total" in self.categories_info[category_name]:
            self.categories_info[category_name]["product_total"] += count_goods
        else:
            self.categories_info[category_name]["product_total"] = count_goods

        print('=================count-----total-------{}==={}'.format(category_name, str(self.categories_info[category_name]["product_total"])))
        print('current----page-----{}---{}'.format(category_name, str(page)))
        if response.text:
            res_len = len(response.text)
            print(res_len)
            if res_len > 500:
                yield self.request_goods_list(category_name, page+1)

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']

        composition_eles = response.xpath('//div[@class="composition"]/ul/li')
        composition_list = []
        for composition_ele in composition_eles:
            composition_text = composition_ele.xpath('text()').get().strip() if composition_ele else ""
            composition_info = composition_text.split(' ') if composition_text else []
            if composition_info:
                composition_list.append({'co_key': composition_info[0], 'co_value': composition_info[1]})

        desc_text = response.xpath('//div[@class="description"]/div/div/p/text()').get()
        ucode = response.xpath('//*[@id="product_code"]/text()').get()
        spu = ucode.split('.')[0]
        goods_item = BaseGoodsItem()
        goods_item['spider_name'] = self.name
        goods_item['model'] = model
        details = json.loads(model.details)
        details["composition_list"] = composition_list
        details["desc_text"] = desc_text
        details["spu"] = spu
        goods_item['details'] = details
        goods_item['asin'] = spu
        yield goods_item


if __name__ == '__main__':
    # strr = '{0:"products",1:"en/clothes-woman",2:"",3:"/en/clothes-woman",4:"M56DUKTUDBHDGRVP8RR8N98Z4GXXG1M5",5:2}'
    # print(base64.encodebytes(strr.encode('utf-8')))
    # encode = "ezA6InByb2R1Y3RzIiwxOiJlbi9jbG90aGVzLXdvbWFuIiwyOiIiLDM6Ii9lbi9jbG90aGVzLXdvbWFuIiw0OiJNNTZEVUtUVURCSERHUlZQOFJSOE45OFo0R1hYRzFNNSIsNTo0fQ=="
    # decode = base64.decodebytes(encode.encode('utf8'))
    # print(decode)
    encode_heml = "<div id=\"pagination_trigger\" data-page=\"2\" data-pagehash=\"b07\" data-cache=\"E6GFF7Z0KV6VUY3JIZ1RP83CDGTD6YRX\"><\/div>"
    print(encode_heml.replace('\t', '').replace('\n', '').replace('\\', ''))

