from scrapy.http import TextResponse
from pyscrapy.extracts.shein import GoodsDetail as XDetail, Common as XShein
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import BaseGoodsItem
from pyscrapy.grabs.shein_goods_reviews import ReviewRequest


class GoodsDetail(BasePage):

    __categories_map = {}

    @property
    def spu(self):
        return self.get_text_by_re(XDetail.re_spu, self.response.text)

    @property
    def title(self):
        return ''

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
        if cls.check_robot_happened(response):
            return False
        meta = response.meta

        cls.__categories_map = meta['categories_map']

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = BaseGoodsItem()

        ele = cls(response)
        item['url'] = ele.url
        item['category_name'] = ele.category_name
        # item['title'] = ele.title
        # item['price_text'] = ele.price_text
        # item['price'] = ele.price

        # if 'asin' not in item:
        #     item['asin'] = ele.asin

        # if 'image' not in item:
        #     image = ele.image
        #     item['image'] = image
        #     item['image_urls'] = [image]

        # details = {}
        # if 'details' in item:
        #     details = item['details']

        # details['items'] = ele.details_items
        # details['sale_at'] = ele.sale_at_text
        # details['asin'] = ele.asin
        # details['rank_list'] = ele.rank_list
        # details['root_rank'] = ele.root_category_rank_num
        # details['root_category_name'] = ele.root_category_name
        # item['details'] = details
        print('=============parse_goods_detail=============end===========')
        spu = ele.spu

        yield ReviewRequest(spu).get_once(page=1, meta={'item': item})
        # yield item
        if 'next_request' in meta:
            yield meta['next_request']

