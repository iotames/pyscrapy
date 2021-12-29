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


class CottononSpider(BaseSpider):

    name = 'cottonon'

    base_url = "https://cottonon.com"
    product_api_url = "https://api.bazaarvoice.com/data/display/0.2alpha/product/summary"

    categories_list = [
        {"name": "men", "url": "https://cottonon.com/AU/men/"},
        {"name": "women", "url": "https://cottonon.com/AU/women/"},
    ]
    limit = 24
    categories_info = {}  # start = 0 sz = 24

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    def __init__(self, name=None, **kwargs):
        super(CottononSpider, self).__init__(name=name, **kwargs)
        self.base_url = "https://" + self.domain
        self.allowed_domains.append("api.bazaarvoice.com")

    def get_product_summary(self, productid: str):
        url_args = {
            "PassKey": "caVdVFPwoIgM0aZNRHGOU6fEFYKO0FqO5BSuRQCMLKy94",
            "productid": productid,
            "contentType": "reviews,questions",
            "reviewDistribution": "primaryRating,recommended",
            "rev": 0,
            "contentlocale": "en*,en_AU"
        }
        return self.product_api_url + "?" + urlencode(url_args)

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for category in self.categories_list:
                name = category.get("name")
                self.categories_info[name] = dict(start=0)
                headers = dict(referer=self.base_url)
                yield Request(
                    category.get("url"),
                    callback=self.parse_goods_list,
                    headers=headers,
                    meta=dict(category_name=name)
                )
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
        if (product_total - start) <= self.limit:
            return True
        return False

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        category_name = meta["category_name"]
        start = self.categories_info[category_name]["start"]
        print('========================start======{}=={}==='.format(category_name, str(start)))
        if start == 0:
            product_total = int(response.xpath('//span[@class="total-product-count"]/text()').extract()[0])
            self.categories_info[category_name]["product_total"] = product_total
        else:
            product_total = self.categories_info[category_name]["product_total"]

        xpath = '//li[@class="grid-tile columns"]/div[@class="product-tile"]'
        eles = response.xpath(xpath)
        for ele in eles:
            # data = ele.xpath("@data-bvproduct").extract()[0]
            # json_data = json.loads(data)
            url = ele.xpath('div[@class="product-image"]/a/@href').extract()[0]
            if not url:
                self.mylogger.debug("==============empty==url===in===={}".format(str(start)))
                continue
            image = ele.xpath('div[@class="product-image"]/a/img/@src').extract()[0]
            title = ele.xpath('div[@class="product-name"]/a/text()').extract()[0].strip()
            color_num_text = ele.xpath('div[@class="product-colors row"]/div/@aria-label').get()
            print(color_num_text)
            color_num = int(color_num_text.split(" ")[0])
            price_text = ele.xpath('div[@class="product-pricing "]/span/@aria-label').get()
            print(price_text)
            price_text = price_text.split("Price ")[1] if price_text else ""
            price = price_text.split(" ")[1] if price_text else 0
            code = url.split("/")[-1].split(".html")[0]  # json_data["productId"]
            spu = code.split("-")[0]
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['url'] = url
            goods_item['code'] = code
            goods_item['asin'] = spu
            goods_item['price'] = price
            goods_item['price_text'] = price_text
            goods_item['title'] = title
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['category_name'] = category_name
            goods_item['details'] = {'color_num': color_num}
            yield goods_item

        if not self.is_last_page(start, product_total):
            self.categories_info[category_name]["start"] += self.limit
            next_start = self.categories_info[category_name]["start"]
            url = response.url
            if start == 0:
                url_args = dict(start=next_start, sz=self.limit)
                url += "?" + urlencode(url_args)
            else:
                url = url.replace("start=" + str(start), "start=" + str(next_start))
            yield Request(
                url,
                callback=self.parse_goods_list,
                meta=dict(category_name=category_name),
                dont_filter=True
            )

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
        yield Request(self.get_product_summary(model.code), callback=self.parse_goods_summary,
                      headers={'referer': self.base_url + "/"},
                      meta=dict(goods_item=goods_item), dont_filter=True)

    def parse_goods_summary(self, response: TextResponse):
        meta = response.meta
        goods_item = meta['goods_item']
        details = goods_item["details"]
        json_data = response.json()
        review_summary = json_data["reviewSummary"]
        reviews_num = review_summary["numReviews"]
        primary_rating = review_summary["primaryRating"]
        recommended = review_summary["recommended"]
        details["recommended_distribution_list"] = recommended["distribution"]  # {count: 211, key: true}
        rating_value = primary_rating["average"]
        goods_item["reviews_num"] = reviews_num
        details["rating_value"] = rating_value
        details["rating_distribution_list"] = primary_rating["distribution"]  # {key: 5, count: 161}
        yield goods_item

