from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import AmazonGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
import re
from pyscrapy.extracts.amazon import GoodsRankingList as XRankingList, GoodsDetail as XDetail
# from translate import Translator


class AmazonSpider(BaseSpider):

    name = 'amazon'
    base_url = "https://www.amazon.com"

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # default 8
        'CONCURRENT_REQUESTS': 8,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    url_params = {
        "language": 'zh_CN'
    }

    top_goods_urls = [
        '/Best-Sellers-Womens-Activewear-Skirts-Skorts/zgbs/fashion/23575633011?{}'
        # '/bestsellers/fashion/2371062011?{}'  # 新品排行榜
        # /new-releases/fashion/2371062011  # 销量排行榜
    ]

    goods_model_list: list

    @staticmethod
    def get_product_code_by_url(url: str) -> str:
        # TODO => extracts.GoodsDetail
        urls = url.split('/')
        index = urls.index('dp')
        return urls[index+1]

    def get_product_url_by_code(self, code: str) -> str:
        # TODO => extracts.GoodsDetail
        if 'pg' in self.url_params:
            del self.url_params['pg']
        return self.base_url + "/dp/{}?{}".format(code, urlencode(self.url_params))

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        # self.allowed_domains.append("api.bazaarvoice.com")

    def start_requests(self):
        for url in self.top_goods_urls:
            self.url_params['pg'] = "1"
            url = self.base_url + url.format(urlencode(self.url_params))
            yield Request(
                url,
                callback=self.parse_top_goods_list,
                headers=dict(referer=self.base_url),
                meta=dict(page=1)
            )

    def parse_top_goods_list(self, response: TextResponse):
        if self.check_robot_happened(response):
            # TODO
            print('check_robot_happened')
            raise RuntimeError('check_robot_happened')
        goods_eles = response.xpath(XRankingList.xpath_goods_items)
        rank_in = 1
        for ele in goods_eles:
            url_ele = ele.xpath(XRankingList.xpath_url)
            if not url_ele:
                print('Skip===============================' + str(rank_in))
                rank_in += 1
                continue
            url = url_ele.get().strip()
            if not url.startswith("http"):
                url = self.base_url + url

            code = self.get_product_code_by_url(url)
            title = ele.xpath(XRankingList.xpath_goods_title).get()
            image = ele.xpath(XRankingList.xpath_goods_img).get()
            review_ele = ele.xpath(XRankingList.xpath_review)
            reviews_num = 0
            if review_ele:
                review_text = review_ele.xpath('text()').get()
                # print('===================review_text=================')
                # print(review_text)
                reviews_num = int(review_text.replace(',', ''))

            model = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.code == code).first()
            goods_item = AmazonGoodsItem()
            goods_item["model"] = model
            goods_item["image"] = image
            goods_item["code"] = code
            goods_item["title"] = title
            goods_item["reviews_num"] = reviews_num
            goods_item["image_urls"] = [image]
            details = {'rank_in': rank_in}
            goods_item["details"] = details
            rank_in += 1
            yield Request(self.get_product_url_by_code(code), callback=self.parse_goods_detail, meta=dict(item=goods_item))

            if response.meta['page'] == 1:
                yield Request(
                    response.url.replace('pg=1', 'pg=2'),
                    callback=self.parse_top_goods_list,
                    meta=dict(page=2)
                )

    @staticmethod
    def check_robot_happened(response: TextResponse):
        xpath_form = '//div[@class="a-box-inner a-padding-extra-large"]/form/div[1]/div/div/h4/text()'
        ele = response.xpath(xpath_form)  # Type the characters you see in this image:
        # print('===============check_robot_happened=======================')
        # print(ele)  # []
        if ele:
            # TODO 切换IP继续爬
            raise RuntimeError("===============check_robot_happened=======================")
        return False

    def parse_goods_detail(self, response: TextResponse):
        item = response.meta['item']
        if self.check_robot_happened(response):
            return False

        price_ele = response.xpath(XDetail.xpath_goods_price)
        price = 0
        if price_ele:
            price_text: str = price_ele.xpath("text()").get()
            price = price_text.split('US$')[1]
            item['price_text'] = price_text
        item['price'] = price

        details_eles = response.xpath(XDetail.xpath_goods_detail_items)
        details = item['details']
        items = []
        for ele in details_eles:
            detail_text = ele.xpath('text()').get().strip()
            items.append(detail_text)
        details['items'] = items
        details['sale_at'] = XDetail.get_goods_detail_feature('上架时间', response)
        details['asin'] = XDetail.get_goods_detail_feature('ASIN', response)

        rank_ele = response.xpath(XDetail.xpath_goods_rank_detail)
        rank_list = []
        root_rank = 0
        if rank_ele:
            rank_list = XDetail.get_goods_rank_list(response)
            text = response.xpath(XDetail.xpath_goods_rank_detail + '[contains(string(),"")]').get()
            root_rank = XDetail.get_rank_num_in_root(text)  # root_rank
        details['rank_list'] = rank_list
        details['root_rank'] = root_rank
        item['details'] = details
        print('=============parse_goods_detail=============end===========')
        print(item)
        yield item

