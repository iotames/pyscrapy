from scrapy.exceptions import UsageError
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import SweatybettyGoodsItem
from ..models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
import re


class SweatybettySpider(BaseSpider):

    name = 'sweatybetty'
    base_url = "https://www.sweatybetty.com"
    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1, default 8
        'CONCURRENT_REQUESTS': 8,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
    }

    goods_model_list: list
    CHILD_GOODS_LIST = 'goods_list'
    CHILD_GOODS_DETAIL = 'goods_detail'
    spider_child = CHILD_GOODS_LIST

    xpath_goods_image = "div/div[@class=\"product-image  \"]/a/img"  # @data-src
    xpath_goods_url = "div/div[@class=\"product-image  \"]/a"  # @href
    xpath_goods_title = "div/div[@class=\"product-tile-details\"]/div[@class=\"product-title\"]/div[@class=\"product-name-grade-wrap\"]/div[@class=\"product-name\"]/a"
    # xpath_goods_rating = "div/div[@class='product-tile-details']/div[@class='product-rating']/div/div/a/div[@class='bv_numReviews_component_container']" // JS render
    xpath_goods_fabric = "//div[@class='pl-text pl-text--p3 fibre-composition-web']"

    def __init__(self, name=None, **kwargs):
        super(SweatybettySpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']
        self.allowed_domains.append("api.bazaarvoice.com")

    url_goods_summary = "https://api.bazaarvoice.com/data/display/0.2alpha/product/summary"
    summary_query = {
        'PassKey': '22spgqyzgh7ktk76n520p3r0q',
        'contentType': 'reviews,questions',
        'reviewDistribution': 'primaryRating,recommended',
        'rev': '0',
        'contentlocale': 'en_GB,en_US,en_AU,en_EU'
    }

    def start_requests(self):

        if self.spider_child == self.CHILD_GOODS_LIST:
            urls = {
                # "all": "https://www.sweatybetty.com/shop?start=0&sz=24&format=load-more",
                "leggings": "https://www.sweatybetty.com/shop/bottoms/leggings?start=0&sz=24&format=load-more",
                "sport-bras": "https://www.sweatybetty.com/shop/underwear/sports-bras?start=0&sz=24&format=load-more",
                "t-shirts": "https://www.sweatybetty.com/shop/tops/t-shirts?start=0&sz=24&format=load-more",
                "jumpers-and-hoodies": "https://www.sweatybetty.com/shop/tops/jumpers-and-hoodies?start=0&sz=24&format=load-more"
            }
            for k, v in urls.items():
                yield Request(
                    v,
                    callback=self.parse_goods_list,
                    headers=dict(referer=v.replace("start=0&sz=24", "start=24&sz=24")),
                    meta=dict(start=0, category_name=k)
                )

        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            # before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(
                Goods.site_id == self.site_id,
                # Goods.updated_at < before_time
            ).all()
            goods_list_len = len(self.goods_model_list)
            print(goods_list_len)
            if goods_list_len > 0:
                yield self.request_detail(0)

    def request_detail(self, model_index: int):
        self.summary_query['productid'] = self.goods_model_list[model_index].code
        return Request(
            self.url_goods_summary + "?" + urlencode(self.summary_query),
            headers={'referer': 'https://www.sweatybetty.com/'},
            callback=self.parse_goods_detail_rating,
            meta=dict(model_index=model_index)
        )

    def parse_goods_detail_page(self, response: TextResponse):
        print('parse_goods_detail_page====================================')
        item = response.meta['item']
        try:
            # TODO GET CATEGORY_NAME
            # re_rule0 = r"\"Viewed Product\",(.+?)\);"  # https://www.gymshark.com/products/gymshark-flex-shorts-black-aw21
            # re_info0 = re.findall(re_rule0, response.text)
            # info0 = json.loads(re_info0[0])

            composition = response.xpath(self.xpath_goods_fabric + "/text()").get().strip()
            fabric = composition.split(":")[1].strip()
            details = item['details']
            details["fabric"] = fabric
            item['details'] = details
            # item['category_name'] = info0['category']
        except AttributeError:
            print("AttributeError: =============================================================")
        yield item

    def parse_goods_detail_rating(self, response: TextResponse):
        model_index = response.meta['model_index']
        text = response.text
        json_response = json.loads(text)
        print(json_response)
        review_summary = json_response['reviewSummary']
        reviews_num = review_summary['numReviews']
        rating_summary = review_summary['primaryRating']
        rating = {
            "average": rating_summary['average']
        }
        for rat_item in rating_summary['distribution']:
            rating[str(rat_item['key'])] = rat_item['count']

        goods_model: Goods = self.goods_model_list[model_index]
        item = SweatybettyGoodsItem()
        item["model"] = goods_model
        item['reviews_num'] = reviews_num
        details = {'rating': rating}
        item['details'] = details

        yield Request(
            goods_model.url,
            callback=self.parse_goods_detail_page,
            headers=dict(referer="https://www.sweatybetty.com/shop"),
            meta=dict(item=item)
            )
        max_goods_index = (len(self.goods_model_list) - 1)
        print('model_index = ' + str(model_index) + '====max_goods_index = ' + str(max_goods_index))
        if model_index < max_goods_index:
            print('next model index ========== ' + str(model_index+1))
            yield self.request_detail(model_index+1)

    @staticmethod
    def get_product_code(li_id: str):
        id1 = li_id.split("-")
        return id1[1]
        # id2 = id1[1]
        # id3 = id2.split("_")
        # return id3[0]

    def parse_goods_list(self, response: TextResponse, **kwargs):
        start = response.meta['start']
        category_name = response.meta['category_name']
        print(start)
        goods_li_eles = response.xpath('//ul[@id="search-result-items"]/li')
        print("items--len=", len(goods_li_eles))
        i = 0
        for ele in goods_li_eles:
            item = SweatybettyGoodsItem()
            li_id = ele.xpath("@id").get("")
            if li_id == "":
                continue
            code = self.get_product_code(li_id)
            model = self.db_session.query(Goods).filter(Goods.code == code, Goods.site_id == self.site_id).first()
            print(code)
            image = ele.xpath(self.xpath_goods_image + "/@data-src").get() + "&fmt=webp"
            print(image)
            url = ele.xpath(self.xpath_goods_url + "/@href").get()
            title = ele.xpath(self.xpath_goods_title + "/text()").get().strip()
            price_text = ele.xpath('div//div[@class="product-price"]/span/text()').get().strip()


            # rating = ele.xpath(self.xpath_goods_rating + "/meta/@content").get()
            # print(rating)

            try:
                price = ele.xpath('div//div[@class="product-price"]/span[1]/@data-price-sales').get()
                print("------try_price----", price)
            except AttributeError as e:
                try:
                    print("---error---AttributeError", e)
                    price = ele.xpath('div//div[@class="product-price"]/span[2]/@data-price-sales').get()
                    print(price)
                    # price_text = ele.xpath('//div[@class="product-price"]/span[2]/text()').get().strip()
                    # print(price_text)
                except AttributeError:
                    continue
            item["model"] = model
            item["image_urls"] = [image]
            item["code"] = code
            item["title"] = title
            item["url"] = url
            item["image"] = image
            item["price"] = price
            item["category_name"] = category_name
            item["price_text"] = price_text
            print(f"--item_detail--category({category_name})--title({title})--price_text({price_text})--url({url})--")
            i += 1
            yield item
        if i == 24:
            # self.base_url + self.goods_list_url.format(str(next_start))
            next_start = start + 24
            yield Request(response.url.replace(f"start={str(start)}", f"start={next_start}"), callback=self.parse_goods_list, meta=dict(start=next_start,category_name=category_name))
