from scrapy.http import TextResponse, Request
from .basespider import BaseSpider
from pyscrapy.items import BaseGoodsItem
# from scrapy.selector import Selector
from pyscrapy.models.Goods import Goods
from Config import Config
from pyscrapy.enum.spider import *
from urllib.parse import urlencode
import time
from sqlalchemy import and_, or_
import json


class KindredbravelySpider(BaseSpider):

    name = NAME_KINDREDBRAVELY

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

    custom_settings = {
        'USER_AGENT': USER_AGENT,
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    def __init__(self, name=None, **kwargs):
        super(KindredbravelySpider, self).__init__(name=name, **kwargs)
        self.image_referer = self.base_url + "/"
        self.allowed_domains.append('9kb7dhflg1-1.algolianet.com')

    API_URL = "https://9kb7dhflg1-1.algolianet.com/1/indexes/*/queries"

    def request_goods_list(self, page: int) -> Request:
        query = {
            'x-algolia-agent': 'Algolia for JavaScript (3.33.0); Browser (lite); react (16.9.0); react-instantsearch (5.7.0); JS Helper (2.28.0)',
            'x-algolia-application-id': '9KB7DHFLG1',
            'x-algolia-api-key': 'a1002aaa5f4abf41651a44cc8d2358b8'
        }
        request_body = r'{"requests":[{"indexName":"shopify_products","params":"query=&hitsPerPage=100&maxValuesPerFacet=10&page=0&highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&distinct=1&facets=%5B%22collections%22%5D&tagFilters=&facetFilters=%5B%5B%22collections%3Aall%22%5D%5D"},{"indexName":"shopify_products","params":"query=&hitsPerPage=1&maxValuesPerFacet=10&page=0&highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&distinct=1&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=collections"}]}'
        url = f"{self.API_URL}?{urlencode(query)}"
        headers = {'referer': self.image_referer}
        return Request(
            url,
            callback=self.parse_goods_list,
            method='POST',
            headers=headers,
            body=request_body,
            meta={'page': page}
        )

    def start_requests(self):

        if self.spider_child == self.CHILD_GOODS_LIST:
            yield self.request_goods_list(page=1)

        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time()
            # if self.app_env == self.spider_config.ENV_PRODUCTION:
            #     before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id, or_(
                    Goods.status == Goods.STATUS_UNKNOWN,
                    Goods.updated_at < before_time)
            )).all()
            goods_list_len = len(self.goods_model_list)
            print('=======goods_list_len============ : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield Request(self.get_site_url(model.url), headers={'referer': self.image_referer},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        data_json = response.json()
        results = data_json['results']
        info = results[0]
        goods_items_list = info['hits']
        for item in goods_items_list:
            # published_at: "2021-01-28 11:44:14 +0100"  or  2022-01-13T06:29:03.000Z

            # desc_html = item['description']
            # select = Selector(text=desc_html)
            # composition_ele = select.xpath('//p[contains(text(), "% ")]')

            status = Goods.STATUS_AVAILABLE if item['inventory_available'] else 0
            image = item['product_image']
            price = item['price']
            spu = item['handle']
            url = self.get_site_url(f"/products/{spu}")
            code = item['id']
            title = item['title']
            desc = item['body_html_safe']
            price_ratio = item['price_ratio']  # 0 or 0.6691449814126395
            size_count = item['variants_count']
            category_name = item['product_type']
            quantity = item['inventory_quantity']

            details = {'rating_value': 0, 'price_ratio': price_ratio, 'size_count': size_count, 'desc': desc}
            goods_item = BaseGoodsItem()
            goods_item['status'] = status
            # goods_item['asin'] = spu  # value too long for asin
            goods_item['spider_name'] = self.name
            goods_item['price'] = price
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = code
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['category_name'] = category_name
            goods_item['quantity'] = quantity
            goods_item['details'] = details
            yield goods_item
        # if response.status == 200 and goods_items_list:
        #     yield self.request_goods_list(page+1)

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model: Goods = meta['model']

        ele_badge = response.xpath('//span[@class="stamped-badge-caption"]')
        ele_revies_num = ele_badge.xpath('@data-reviews')
        ele_rating_value = ele_badge.xpath('@data-rating')
        reviews_num = int(ele_revies_num.get()) if ele_revies_num else 0
        rating_value = float(ele_rating_value.get()) if ele_rating_value else 0

        goods_item = BaseGoodsItem()
        goods_item['spider_name'] = self.name
        goods_item['model'] = model
        goods_item['reviews_num'] = reviews_num

        details = json.loads(model.details)
        details["rating_value"] = rating_value
        goods_item['details'] = details

        yield goods_item

