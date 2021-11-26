from scrapy.http import TextResponse
from pyscrapy.extracts.amazon import GoodsDetail as XDetail
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import AmazonGoodsItem


class AmazonGoodsDetail(BasePage):

    __rank_html = None

    @property
    def image(self):
        return self.get_text(XDetail.xpath_goods_image)

    @property
    def title(self):
        return self.get_text(XDetail.xpath_goods_title)

    @property
    def price_text(self) -> str:
        ele = self.response.xpath(XDetail.xpath_goods_price)
        if not ele:
            return ''
        return ele.get().strip()

    @property
    def price(self):
        if not self.price_text:
            return 0
        info = self.price_text.split('US$')
        if len(info) > 1:
            return info[1]
        return 0

    @property
    def details_items(self) -> list:
        items = []
        for ele in self.response.xpath(XDetail.xpath_goods_detail_items):
            detail_text = ele.get().strip()
            if detail_text:
                items.append(detail_text)
        return items

    @property
    def rank_html(self) -> str:
        if self.__rank_html is not None:
            return self.__rank_html
        self.__rank_html = XDetail.get_rank_html(self.response)
        return self.__rank_html

    @property
    def rank_list(self) -> list:
        if self.rank_html:
            return XDetail.get_goods_rank_list(self.response)
        return []

    @property
    def root_category_name(self) -> str:
        if self.rank_html:
            return XDetail.get_root_category_name(self.rank_html)
        return ''

    @property
    def root_category_rank_num(self) -> int:
        if self.rank_html:
            return XDetail.get_rank_num_in_root(self.rank_html)
        return 0

    @property
    def asin(self) -> str:
        return XDetail.get_goods_detail_feature('ASIN', self.response)

    @property
    def sale_at_text(self) -> str:
        return XDetail.get_goods_detail_feature('上架时间', self.response)

    @classmethod
    def parse(cls, response: TextResponse):
        if cls.check_robot_happened(response):
            return False
        meta = response.meta

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = AmazonGoodsItem()

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

