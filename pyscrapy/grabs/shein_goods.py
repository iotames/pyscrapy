from scrapy.http import TextResponse
from pyscrapy.extracts.shein import GoodsDetail as XDetail
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import BaseGoodsItem


class GoodsDetail(BasePage):

    __rank_html = None

    @property
    def spu(self):
        return self.get_text_by_re(XDetail.re_spu, self.response.text)

    @property
    def title(self):
        return self.get_text(XDetail.xpath_goods_title)


    @classmethod
    def parse(cls, response: TextResponse):
        if cls.check_robot_happened(response):
            return False
        meta = response.meta

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = BaseGoodsItem()

        ele = cls(response)
        item['url'] = response.url
        item['title'] = ele.title
        item['price_text'] = ele.price_text
        item['price'] = ele.price

        if 'asin' not in item:
            item['asin'] = ele.asin

        if 'image' not in item:
            image = ele.image
            item['image'] = image
            item['image_urls'] = [image]

        details = {}
        if 'details' in item:
            details = item['details']

        details['items'] = ele.details_items
        details['sale_at'] = ele.sale_at_text
        details['asin'] = ele.asin
        details['rank_list'] = ele.rank_list
        details['root_rank'] = ele.root_category_rank_num
        details['root_category_name'] = ele.root_category_name
        item['details'] = details
        print('=============parse_goods_detail=============end===========')
        print(item)
        yield item
        if 'next_request' in meta:
            yield meta['next_request']

