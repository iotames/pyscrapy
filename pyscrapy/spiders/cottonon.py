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
# 子元素内使用.xpath方法，字符串参数不能以//开头


class CottononSpider(BaseSpider):

    name = 'cottonon'

    base_url = "https://cottonon.com"
    product_api_url = "https://api.bazaarvoice.com/data/display/0.2alpha/product/summary"

    categories_list = [
        {'gender': 'Women', "name": "Bras", "url": "https://cottonon.com/AU/co/women/womens-lingerie/bras/"},
        {'gender': 'Women', "name": "Tights", "url": "https://cottonon.com/AU/co/women/womens-activewear/gym-tights/"},
        {'gender': 'Women', "name": "Fleece & Sweats", "url": "https://cottonon.com/AU/co/women/womens-clothing/womens-hoodies-jumpers/"},
        {'gender': 'Women', "name": "Graphic T-Shirts", "url": "https://cottonon.com/AU/co/women/womens-clothing/womens-graphic-tees/"},
    ]

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
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
                headers = dict(referer=self.base_url)
                yield Request(
                    category.get("url"),
                    callback=self.parse_goods_list,
                    headers=headers,
                    meta=dict(category_name=name, start=0)
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

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        category_name = meta["category_name"]
        start = meta["start"]
        nds = response.xpath('//li[@class="grid-tile pagination-item columns"]')
        i = 1
        for nd in nds:
            code = nd.xpath("@data-colors-to-show").get("")
            self.mylogger.debug(f"--start({start})-begin({i})--code({code})----")
            if code == "":
                continue
            spu = code.split("-")[0]
            title = nd.xpath('div//a[@class="name-link"]/text()').get().strip()
            url = nd.xpath('div//a[@class="name-link"]/@href').get()
            # // div[@class="product-name "] 子元素内使用.xpath方法，字符串参数不能以//开头

            # url_split = url.split('originalPid=')
            # if len(url_split) == 2:
            #     code = url_split[1]
            # else:
            code = self.get_guid_by_url(url)
            image = nd.xpath('div//div[@class="product-image"]//img/@src').get("")
            price_text1 = nd.xpath('div//span[@class="product-sales-price"]/text()').get().strip()
            price_text2 = nd.xpath('div//span[@class="product-sales-price"]/sup/text()').get()
            price_text = price_text1 + price_text2
            # print("-----price_text", price_text)
            price = price_text.split('$')[1]
            old_price = price
            old_price_text1 = nd.xpath('div//span[@class="product-standard-price"]/text()').get("").strip()
            if old_price_text1 != "":
                old_price_text2 = nd.xpath('div//span[@class="product-standard-price"]/sup/text()').get("")
                old_price_text = old_price_text1 + old_price_text2
                old_price = old_price_text.split('$')[1]
            # print("-----price--old_price", price, old_price)
            color_num_text = nd.xpath('div//div[@class="product-colours-available"]/@aria-label').get().strip()
            # print("-----color_num_text-----", color_num_text)
            color_num = int(color_num_text.split(" ")[0])

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
            goods_item['details'] = {'color_num': color_num, 'old_price': old_price}
            self.mylogger.debug(f"--goods_item--{start}-{i}--code({code})--title({title})--price({price})--url({url})--")
            i += 1
            yield goods_item

        currentUrl = response.url
        limit = 60
        if len(nds) == limit:
            next_url = ''
            next_start = start + limit
            if start == 0:
                next_url = response.url+'?start=60&sz=60'
            else:
                next_url = response.url.replace(f'start={start}', f'start={next_start}')
            print("-----next_page_url------------", next_url)
            yield Request(
                next_url, callback=self.parse_goods_list, meta=dict(category_name=category_name, start=next_start), dont_filter=True
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
