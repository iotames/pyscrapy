from scrapy.http import TextResponse
from pyscrapy.extracts.shein import GoodsDetail as XDetail, Common as XShein
from pyscrapy.grabs.basegrab import BaseResponse
from pyscrapy.items import BaseGoodsItem
from pyscrapy.grabs.shein_goods_reviews import ReviewRequest
import json


class GoodsDetail(BaseResponse):

    __categories_map = {}

    __price_json = {}
    __intro_data = {}

    def __get_price_json(self) -> dict:
        str1 = self.get_text_by_re(XDetail.re_price, self.response.text)
        if str1:
            str2 = "{" + str1 + "}}"
            return json.loads(str2)
        return {}

    def __get_product_intro_data(self) -> dict:
        str1 = self.get_text_by_re(XDetail.re_product_intro_data, self.response.text)
        if str1:
            return json.loads(str1)
        return {}

    @property
    def origin_data(self):
        if not self.__intro_data:
            self.__intro_data = self.__get_product_intro_data()
        return self.__intro_data

    @property
    def color(self) -> dict:
        detail = self.origin_data['detail']
        goods = {'goods_id': detail['goods_id']}
        for attr in detail['productDetails']:
            if attr['attr_name_en'] == 'Color':
                goods['color'] = attr['attr_value_en']
                break
        return goods

    @property
    def relation_colors(self) -> list:
        rela_colors = self.__intro_data['relation_color']
        colors = []
        if not rela_colors:
            return colors
        for goods in rela_colors:
            color_text = ''
            for attr in goods['productDetails']:
                if attr['attr_name_en'] == 'Color':
                    color_text = attr['attr_value_en']
                    break
            detail = {
                'goods_id': goods['goods_id'],
                'color': color_text,
            }
            colors.append(detail)
        return colors

    @property
    def spu(self):
        return self.get_text_by_re(XDetail.re_spu, self.response.text)

    @property
    def brand(self):
        return self.origin_data['detail']['brand']
        # return self.get_text_by_re(XDetail.re_brand, self.response.text)

    @property
    def price_text(self) -> str:
        if self.origin_data:
            return self.origin_data['detail']['salePrice']['usdAmountWithSymbol']
        return ''
        # if not self.__price_json:
        #     self.__price_json = self.__get_price_json()
        # return self.__price_json["salePrice"]["amountWithSymbol"]

    @property
    def price(self):
        # if not self.__price_json:
        #     self.__price_json = self.__get_price_json()
        # return self.__price_json["salePrice"]["amount"]
        if self.origin_data:
            return self.origin_data['detail']['salePrice']['usdAmount']
        return 0

    @property
    def title(self):
        return self.get_text(XDetail.xpath_title)

    @property
    def url(self):
        return self.response.url

    @property
    def cat_id(self):
        return XShein.get_cat_id_by_url(self.url)

    @property
    def category_name(self):
        if self.cat_id in self.__categories_map:
            return self.__categories_map[self.cat_id]['cat_name']
        return ''

    @classmethod
    def parse(cls, response: TextResponse):
        meta = response.meta
        print('=======goods=======' + response.url + '========count = ' + str(meta['count']))

        cls.__categories_map = meta['categories_map']

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = BaseGoodsItem()

        ele = cls(response)
        item['url'] = ele.url
        item['category_name'] = ele.category_name
        item['title'] = ele.title
        item['price_text'] = ele.price_text
        item['price'] = ele.price

        # if 'image' not in item:
        #     image = ele.image
        #     item['image'] = image
        #     item['image_urls'] = [image]

        details = {}
        if 'details' in item:
            details = item['details']

        spu = ele.spu
        details['spu'] = spu
        details['color'] = ele.color
        details['relation_colors'] = ele.relation_colors
        # details['asin'] = ele.asin
        item['details'] = details
        print('=============parse_goods_detail=============end===========')

        yield ReviewRequest.get_once(data={'spu': spu}, meta={'item': item, 'goods_url': response.url})
        # yield item
        if 'next_request' in meta:
            yield meta['next_request']

