import re
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from pyscrapy.enum.spider import *
from urllib.parse import urlencode
from scrapy.selector import Selector, SelectorList
from time import strptime, mktime, time
from datetime import datetime
from pyscrapy.items import GoodsReviewShefitItem


class ShefitSpider(BaseSpider):

    name = 'shefit'

    base_url = "https://shefit.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    def __init__(self, name=None, **kwargs):
        super(ShefitSpider, self).__init__(name=name, **kwargs)
        self.base_url = "https://" + self.domain
        self.image_referer = self.base_url + "/"
        self.allowed_domains.append("staticw2.yotpo.com")

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST:
            url = self.get_site_url('/collections/shefit')
            yield Request(
                url,
                callback=self.parse_goods_list,
                headers=dict(referer=self.base_url)
            )

        if self.spider_child == CHILD_GOODS_DETAIL:
            url = self.input_args.get('url', None)
            if url:
                headers = {'referer': self.image_referer}
                goods_model = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.url == url).first()
                yield Request(url, self.parse_goods_detail, headers=headers, meta=dict(goods_model=goods_model))
            else:
                request_list = self.request_list_goods_detail()
                for req in request_list:
                    yield req

        if self.spider_child == CHILD_GOODS_REVIEWS:
            url = "https://shefit.com/products/leggings-boss"  # self.input_args.get('url')
            goods_model = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.url == url).first()
            meta = dict(goods_model=goods_model)
            yield self.request_goods_reviews(1, meta)

    def request_goods_reviews(self, page: int, meta: dict) -> Request:
        reviews_url = "https://staticw2.yotpo.com/batch/app_key/dqbG40YNTpcZQTZ7u680Wus6Gn2HzVmK7219GsNM/domain_key/2263121592374/widget/reviews"
        # [{"method":"reviews","params":{"pid":"2263121592374","order_metadata_fields":{},"widget_product_id":"2263121592374",
        # "data_source":"default","page":1,"host-widget":"main_widget","is_mobile":false,"pictures_per_review":10}}]
        methods = [{
            "method": "reviews",
            "params": {"pid": "2263121592374", "order_metadata_fields": {},
                       "widget_product_id": "2263121592374", "data_source": "default", "page": page,
                       "host-widget": "main_widget", "is_mobile": False, "pictures_per_review": 10
                       }
        }]
        post_data = {
            "methods": json.dumps(methods, separators=(',', ':')),
            "app_key": "dqbG40YNTpcZQTZ7u680Wus6Gn2HzVmK7219GsNM",
            "is_mobile": False,
            "widget_version": "2022-01-12_12-39-56"
        }
        # print(post_data)
        body = urlencode(post_data)
        # print(body)
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "referer": self.image_referer
        }
        # print(headers)
        meta['page'] = page
        return Request(url=reviews_url, method='POST', callback=self.parse_goods_reviews, meta=meta,
                       body=body, headers=headers)

    goods_list_count = 0

    def parse_goods_list(self, response: TextResponse):
        xpath = '//div[@class="twelve columns medium-down--one-whole"]/script/text()'
        json_text = response.xpath(xpath).get()

        json_info = json.loads(json_text)
        goods_items = json_info['itemListElement']
        goods_list_len = len(goods_items)  # 43
        print('=========total goods =======' + str(goods_list_len))
        for goods in goods_items:
            print(goods)
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['title'] = goods['name']
            goods_item['url'] = goods['url']
            yield goods_item

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

        re_rule = r"productVariants=(.+?);"
        re_info = re.findall(re_rule, response.text)
        text = re_info[0]
        product_variants = json.loads(text)
        print(product_variants)
        quantity = 0
        sku_list = []
        for product in product_variants:
            sku_inventory = product['inventory_quantity']
            sku_info = {'title': product['title'], 'sku': product['sku'], 'name': product['name'], 'quantity': sku_inventory}
            sku_list.append(sku_info)
            quantity += sku_inventory

        details = {
            'sku_list': sku_list
        }

        xpath_json = '//script[@type="application/ld+json"]/text()'
        json_product_text = response.xpath(xpath_json)[1].get()
        # print('======json_product_text===========')
        # print(json_product_text)
        p_info = json.loads(json_product_text, strict=False)
        print(p_info)
        title = p_info['name']
        url = p_info['url']
        # sku_code = p_info['sku']  # 140003-011
        desc = p_info['description']
        image_text: str = p_info['image'][0]
        image_text = image_text.split('?')[0]
        last_str = image_text.split('_')[-1]
        img_ext = last_str.split('.')[-1]  # jpg gif
        image = image_text.replace(last_str, '200x.' + img_ext)
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

        goods_item = BaseGoodsItem()
        goods_item['model'] = goods_model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        goods_item['image'] = image
        goods_item['code'] = code
        goods_item['title'] = title
        goods_item['image_urls'] = [image]
        goods_item['url'] = response.url
        goods_item['price'] = price
        goods_item['price_text'] = price_text
        # goods_item['reviews_num'] = reviews_num
        goods_item['status'] = status
        goods_item['details'] = details
        goods_item['quantity'] = quantity
        yield goods_item

    def get_review_fields(self, eles) -> list:
        item_list = []
        for ele in eles:
            code = ele.xpath("@data-review-id").get()
            review_time = 0
            review_date = None
            print("==============review=====user_fields_eles===============")
            xpath_sku = 'div[@class="yotpo-footer "]//a[@class="grouping-reference-link"]/text()'
            xpath_header = 'div[@class="yotpo-header yotpo-verified-buyer "]'
            xpath_date = xpath_header + '/div[@class="yotpo-header-element yotpo-header-actions "]/span/text()'
            ele_date = ele.xpath(xpath_date)
            time_text = ele_date.get() if ele_date else ""
            ele_sku = ele.xpath(xpath_sku)
            sku_text = ele_sku.get() if ele_sku else ""

            if time_text:
                dt = time_text.split('/')
                date_fixed = f"20{dt[2]}-{dt[0]}-{dt[1]}"
                time_format = "%Y-%m-%d"
                review_time = mktime(strptime(date_fixed, time_format))
                review_date = datetime.strptime(date_fixed, time_format)
            xpath_title = 'div[@class="yotpo-main "]//div[@class="content-title yotpo-font-bold"]/text()'
            xpath_body = 'div[@class="yotpo-main "]//div[@class="content-review"]/text()'
            ele_title = ele.xpath(xpath_title)
            ele_body = ele.xpath(xpath_body)
            title = ele_title.get() if ele_title else ""
            body = ele_body.get() if ele_body else ""
            # print(f"=====title==and==body===\n{title}\n{body}")
            xpath_stars = xpath_header + '/div[@class="yotpo-header-element "]/div[@class="yotpo-review-stars "]'
            xpath_rating = xpath_stars + '/span[@class="sr-only"]/text()'
            star_text_ele = ele.xpath(xpath_rating)
            star_text = star_text_ele.get() if star_text_ele else ""
            rating_value = star_text.split(" ")[0] if star_text else 0
            # print(f"==rating_value=={star_text}===")
            xpath_user_field = xpath_stars + '/div[@class="yotpo-user-related-fields"]/div[@class="yotpo-user-field"]'
            user_fields_eles = ele.xpath(xpath_user_field)
            age, activity, body_type = ("", "", "")
            for user_field_ele in user_fields_eles:
                key_ele = user_field_ele.xpath('span[@class="yotpo-user-field-description text-s"]/text()')
                key_text = key_ele.get().replace(":", "") if key_ele else ""
                value_ele = user_field_ele.xpath('span[@class="yotpo-user-field-answer text-s"]/text()')
                value_text = value_ele.get() if value_ele else ""
                if key_text == "Age":
                    age = value_text
                if key_text == "Activity":
                    activity = value_text
                if key_text == "BODY TYPE":
                    body_type = value_text
                # print(f"=={key_text}==={value_text}===")
            item = GoodsReviewShefitItem()
            item['code'] = code
            item['age'] = age
            item['activity'] = activity
            item['body_type'] = body_type
            item['title'] = title
            item['body'] = body
            item['sku_text'] = sku_text
            item['rating_value'] = rating_value
            item['review_time'] = review_time
            item['review_date'] = review_date
            item['time_str'] = time_text
            item_list.append(item)
        return item_list

    def parse_goods_reviews(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        goods_model = meta['goods_model']
        print(f"===============page={str(page)}=========")
        html = response.json()[0]['result']

        select = Selector(text=html)
        # <div class="yotpo-review yotpo-regular-box yotpo-regular-box-filters-padding " data-review-id="306840408">
        reviews_eles = select.xpath('//div[@class="yotpo-review yotpo-regular-box  "]')
        reviews_eles_first = select.xpath('//div[@class="yotpo-review yotpo-regular-box yotpo-regular-box-filters-padding "]')

        for itemfirst in self.get_review_fields(reviews_eles_first):
            itemfirst['goods_id'] = goods_model.id
            itemfirst['goods_code'] = goods_model.code
            yield itemfirst
        print("==========first===end=============================================================")
        for item in self.get_review_fields(reviews_eles):
            item['goods_id'] = goods_model.id
            item['goods_code'] = goods_model.code
            yield item

        next_page = page + 1
        ele_next_page = select.xpath(f"//a[@role=\"menuitem\"][@data-page=\"{str(next_page)}\"]")
        if ele_next_page:
            yield self.request_goods_reviews(next_page, meta)


